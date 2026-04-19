from datetime import date, datetime

from fastapi import APIRouter
from redis.asyncio import Redis

from app.core import config
from app.models.slot import Slot
from app.schemas.slot import SlotResponse

router = APIRouter(prefix="/slots", tags=["Slots"])

# Redis connection pool
redis_client: Redis = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)


# @router.get("/{slot_id}", response_model=AppointmentSlotResponse)
# async def api_get_slot(
#         slot_id: int,
# ):
#     return AppointmentSlotResponse()


# @router.post("/", response_model=SlotResponse, status_code=status.HTTP_201_CREATED)
# async def api_make_slot(
#         slot_request: SlotRequest,
# ):
#     return SlotResponse()
#
# # Should be idempotent
# @router.patch("/", response_model=SlotResponse, status_code=status.HTTP_201_CREATED)
# async def api_make_slot(
#         slot_request: SlotUpdateRequest,
# ):
#     return SlotResponse()

# @router.patch("/active", response_model=SlotResponse, status_code=status.HTTP_200_OK)
# async def api_make_slot(
#         slot_request: SlotActiveTypeUpdateRequest,
# ):
#     # role이 faculty 아니면 403 error
#     # slot_id -> hospital_id -> user_hospitals로 권한 있는지 확인
#     return SlotResponse()


@router.get("")
async def list_available_slots(
        hospital_id: int | None = None,
        doctor_id: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
) -> list[SlotResponse]:
    """
    List available appointment slots with filtering.
    """
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
