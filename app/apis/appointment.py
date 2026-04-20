import asyncio
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from redis.asyncio import Redis
from tortoise.transactions import in_transaction

from app.core import config
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


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
        data: AppointmentRequest,
        user_id: int,
        # user: User = Depends(get_current_user),
) -> AppointmentResponse:
    user = await User.get_or_none(id=user_id)

    # 1. Idempotency Check (DB level)
    existing: Appointment | None = await Appointment.get_or_none(idempotency_key=data.idempotency_key)
    if existing:
        return existing

    # 2. Duplicate Check for same user and slot (DB level)
    if await Appointment.exists(user=user, slot_id=data.slot_id, status=AppointmentStatus.CONFIRMED):
        raise HTTPException(status_code=400, detail="Already booked for this slot")

    # 3. Distributed Lock (Redis) to prevent race conditions on high traffic
    lock_key: str = f"lock:slot:{data.slot_id}"
    lock_value: str = f"{user.id}:{data.idempotency_key}"

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
            slot: Slot | None = await Slot.select_for_update().get_or_none(id=data.slot_id)
            if not slot:
                raise HTTPException(status_code=404, detail="Slot not found")

            if not slot.is_active:
                raise HTTPException(status_code=400, detail="Slot is not active")

            if slot.remains <= 0:
                raise HTTPException(status_code=400, detail="No capacity left in this slot")

            # 5. Create Appointment
            appointment: Appointment = await Appointment.create(
                idempotency_key=data.idempotency_key,
                user=user,
                slot=slot,
                hospital_id=slot.hospital_id,
                start_at=slot.start_at,
                end_at=slot.end_at,
                status=AppointmentStatus.CONFIRMED,
                memo=data.memo,
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
