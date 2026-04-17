from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.models.slot import SlotType
from app.schemas.frozen_config import FROZEN_RESPONSE_CONFIG


class AppointmentSlotResponse(BaseModel):
    id: int
    hospital_id: int
    doctor_id: Annotated[int | None, Field(default=None)]
    type: SlotType
    capacity: int
    remains: int
    start_at: datetime
    end_at: datetime
    slot_duration_minutes: int
    is_active: bool

    model_config = FROZEN_RESPONSE_CONFIG

