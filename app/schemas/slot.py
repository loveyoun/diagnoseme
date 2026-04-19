from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from app.models.slot import SlotType
from app.schemas.frozen_config import FROZEN_RESPONSE_CONFIG, FROZEN_CONFIG


class SlotRequest(BaseModel):
    hospital_id: int
    doctor_id: Annotated[int | None, Field(default=None)]
    type: Annotated[SlotType, Field(default="hot")]
    capacity: int
    remains: int
    start_at: datetime
    end_at: datetime
    slot_duration_minutes: int

    model_config = FROZEN_CONFIG


class SlotUpdateRequest(BaseModel):
    hospital_id: int | None
    doctor_id: int | None
    capacity: int | None
    remains: int | None
    start_at: datetime | None
    end_at: datetime | None
    slot_duration_minutes: int | None

    model_config = FROZEN_CONFIG

# Idempotent API
class SlotActiveTypeUpdateRequest(BaseModel):
    slot_id: int

    model_config = FROZEN_CONFIG


class SlotResponse(BaseModel):
    id: int
    hospital_id: int
    doctor_id: int | None
    type: SlotType
    capacity: int
    remains: int
    start_at: datetime
    end_at: datetime
    slot_duration_minutes: int
    is_active: bool

    model_config = FROZEN_RESPONSE_CONFIG
