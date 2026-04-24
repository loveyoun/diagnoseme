import time
from datetime import datetime, date

from fastapi import APIRouter, status, Depends, HTTPException
from redis.asyncio import Redis

from app.core import get_redis
from app.models.slot import Slot
from app.schemas.slot import SlotResponse, SlotRequest, SlotTypeActiveUpdateRequest

router = APIRouter(prefix="/slots", tags=["Slots"])
SLOT_MEMBER_BUFFER_SECONDS = 3600  # 버퍼 1시간


# 완
@router.get("/{slot_id}", response_model=SlotResponse)
async def api_get_slot(slot_id: int) -> SlotResponse:
    return Slot.get_by_id(slot_id)


# 완
@router.post("", response_model=SlotResponse, status_code=status.HTTP_201_CREATED)
async def api_make_slot(slot_req: SlotRequest) -> SlotResponse:
    """ @Idempotency """
    return await Slot.create_slot(slot_req)


@router.patch("/active", response_model=SlotResponse, status_code=status.HTTP_200_OK)
async def api_make_slot(
        slot_tau_request: SlotTypeActiveUpdateRequest,
        redis: Redis = Depends(get_redis),
        # slot_id -> hospital_id -> user_hospitals로 faculty 권한 있는지 확인(or 403 ERROR)
):
    slot_id = slot_tau_request.slot_id

    """ 정상작동하면 SlotService로 떼기 """
    slot: Slot | None = Slot.get_by_id(slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    # TTL 계산
    key = f"slot:{slot_id}"
    ttl = int(slot.end_at.timestamp()) + SLOT_MEMBER_BUFFER_SECONDS - int(time.time())
    if ttl <= 0:
        raise HTTPException(status_code=400, detail="Slot already expired")

    # DB가 source of truth
    await slot.activate_with_instance()
    async with redis.pipeline() as pipe:
        pipe.hset(key, mapping={
            "capacity": slot.capacity,
            "ttl": ttl
        })
        pipe.expire(key, ttl)
        await pipe.execute()
    """"""

    return slot


# @router.patch("/", response_model=SlotResponse, status_code=status.HTTP_201_CREATED)
# async def api_make_slot(
#         slot_request: SlotUpdateRequest,
# ):
#     return SlotResponse()


# Pagination
@router.get("")
async def list_available_slots(
        hospital_id: int | None = None,
        doctor_id: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
) -> list[SlotResponse]:
    query = Slot.filter(is_active=True, remains__gt=0)

    if hospital_id:
        query = query.filter(hospital_id=hospital_id)
    if doctor_id:
        query = query.filter(doctor_id=doctor_id)
    if start_date:
        query = query.filter(start_at__gte=datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(start_at__lte=datetime.combine(end_date, datetime.max.time()))

    slots: list[Slot] = await query.order_by("start_at").all()
    return slots
