import asyncio
from datetime import datetime
from urllib.request import Request

from fastapi import APIRouter, HTTPException, status
from redis.asyncio import Redis
from tortoise.transactions import in_transaction

from app.core import config
from app.core.admission_control import AdmissionControl, SlotResult
from app.core.rate_limiter import TokenBucketRateLimiter
from app.core.stream_producer import stream_enqueue_appointment
from app.models.appointment import Appointment, AppointmentStatus
from app.models.slot import Slot
from app.models.user import User
from app.schemas.appointment import (
    AppointmentCancelRequest,
    AppointmentRequest,
    AppointmentResponse,
)

router = APIRouter(prefix="/appointments", tags=["Appointments"])

# Redis connection pool
redis_client: Redis = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)


@router.post("/v1", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
        appt_req: AppointmentRequest,
        user_id: int,
        # user: User = Depends(get_current_user),
) -> AppointmentResponse:
    user = await User.get_by_id(user_id=user_id)

    # 1. Idempotency Check (DB level)
    existing: Appointment | None = await Appointment.get_by_idem_key(idem_key=appt_req.idemp_key)
    if existing:
        return existing

    # 2. Duplicate Check for same user and slot (DB level)
    if await Appointment.exists(user=user, slot_id=appt_req.slot_id, status=AppointmentStatus.CONFIRMED):
        raise HTTPException(status_code=400, detail="Already booked for this slot")

    # 3. Distributed Lock (Redis) to prevent race conditions on high traffic
    lock_key: str = f"lock:slot:{appt_req.slot_id}"
    lock_value: str = f"{user.id}:{appt_req.idempotency_key}"

    # Try to acquire lock for 10 seconds
    acquired: bool = await redis_client.set(lock_key, lock_value, ex=10, nx=True)
    if not acquired:
        # Retry logic or wait
        for _ in range(5):
            await asyncio.sleep(0.1)
            acquired = await redis_client.set(lock_key, lock_value, ex=10, nx=True)
            if acquired:
                break
        else:
            raise HTTPException(status_code=429, detail="Server is busy, please try again later")

    try:
        async with in_transaction() as conn:
            # 4. Capacity Check and Reservation (DB Lock)
            slot: Slot | None = await Slot.select_for_update().get_or_none(id=appt_req.slot_id)
            if not slot:
                raise HTTPException(status_code=404, detail="Slot not found")

            if not slot.is_active:
                raise HTTPException(status_code=400, detail="Slot is not active")

            if slot.remains <= 0:
                raise HTTPException(status_code=400, detail="No capacity left in this slot")

            # 5. Create Appointment
            appointment: Appointment = await Appointment.create(
                idemp_key=appt_req.idemp_key,
                user=user,
                slot=slot,
                hospital_id=slot.hospital_id,
                start_at=slot.start_at,
                end_at=slot.end_at,
                status=AppointmentStatus.CONFIRMED,
                memo=appt_req.memo,
                using_db=conn
            )

            # 6. Decrease remains
            slot.remains -= 1
            await slot.save(using_db=conn)

            return appointment

    finally:
        # Release lock only if we were the one who held it
        current_lock_val: str | None = await redis_client.get(lock_key)
        if current_lock_val == lock_value:
            await redis_client.delete(lock_key)


# ─────────────────────────────────────────────
# 1. Idempotency 체크 (캐시 히트 시 즉시 반환)
# 2. Global rate limit (Lua 토큰버킷)
# 3. 슬롯 중복/정원 체크 (Lua SET)
# 4. Stream 발행
# ─────────────────────────────────────────────
@router.post("/v2", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
        appointment_req: AppointmentRequest,
        user_id: int,
        # user: User = Depends(get_current_user),
        request: Request,
) -> dict[str, str]:
    slot_id: int = appointment_req.slot_id
    memo: str = appointment_req.memo
    idem_key: str = appointment_req.idem_key
    user = await User.get_by_id(user_id=user_id)

    redis: Redis = redis_client
    global_limiter = TokenBucketRateLimiter(redis, capacity=1000, refill_rate=100)
    user_limiter = TokenBucketRateLimiter(redis, capacity=10, refill_rate=1)
    admission = AdmissionControl(redis)

    # ── Step 0: Global rate limit ─────────────────
    await global_limiter.enforce("ratelimit:global")

    # ── Step 1: Idempotency (Admission Control) ──────────────────
    cached = await admission.check_idempotency(user_id, idem_key)
    if cached:
        if cached.status == "processing":
            return {"status": "processing", "poll_url": f"/reservations/{idem_key}"}
        return {"status": cached.status, **cached.result}

    # ── Step 2: User rate limit (두 개 중 하나라도 거절 시 차단)─────────────────
    await user_limiter.enforce(f"ratelimit:user:{user_id}")

    # ── Step 3: 슬롯 정원/중복 체크 ──────────────
    slot_capacity = 3  # 슬롯당 최대 3명 (설정값으로 분리 권장)
    slot_ttl = 3600  # 슬롯 만료까지 1시간 (실제론 DB에서 조회)

    slot_result = await admission.try_reserve_slot(
        slot_id, user_id, slot_capacity, slot_ttl
    )

    if slot_result == SlotResult.ALREADY_RESERVED:
        raise HTTPException(409, {"error": "already_reserved", "slot_id": slot_id})
    if slot_result == SlotResult.FULL:
        raise HTTPException(409, {"error": "slot_full", "slot_id": slot_id})

    # ── Step 4: 처리 중 마킹 + Stream 발행 ────────
    await admission.mark_processing(user_id, idem_key)
    msg_id = await stream_enqueue_appointment(redis, user_id, slot_id, idem_key)

    return {
        "status": "processing",
        "message_id": msg_id,
        "poll_url": f"/appointments/{idem_key}",

        # SSE를 원하면 클라이언트가 선택적으로 연결
        "sse_url": f"/appointments/{idem_key}/stream",
    }


@router.post("/{appointment_id}/cancel", response_model=AppointmentResponse)
async def cancel_appointment(
        appointment_id: int,
        data: AppointmentCancelRequest,
        user_id: int,
        # user: User = Depends(get_current_user),
) -> AppointmentResponse:
    async with in_transaction() as conn:
        user = await User.get_or_none(id=user_id)

        appointment: Appointment | None = await Appointment.select_for_update().get_or_none(id=appointment_id,
                                                                                            user=user)
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")

        if appointment.status == AppointmentStatus.CANCELLED:
            return appointment

        # Increase slot remains
        slot: Slot | None = await Slot.select_for_update().get_or_none(id=appointment.slot_id)
        if slot:
            slot.remains += 1
            await slot.save(using_db=conn)

        appointment.status = AppointmentStatus.CANCELLED
        appointment.cancelled_at = datetime.utcnow()
        appointment.cancelled_by = user
        if data.cancel_reason_id:  # user을 cancelled_by에 넣어주어야 한다.
            appointment.cancel_reason_id = data.cancel_reason_id

        await appointment.save(using_db=conn)
        return appointment
