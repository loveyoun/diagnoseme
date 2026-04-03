from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.models.slot import SlotType


class AppointmentSlotResponse(BaseModel):
    id: Annotated[int, Field(description="Slot ID")]
    hospital_id: Annotated[int, Field(description="Hospital ID")]
    doctor_id: Annotated[int | None, Field(default=None, description="Doctor ID")]
    type: Annotated[SlotType, Field(description="Slot type")]
    capacity: Annotated[int, Field(description="Total capacity")]
    remains: Annotated[int, Field(description="Remaining capacity")]
    start_at: Annotated[datetime, Field(description="Start time")]
    end_at: Annotated[datetime, Field(description="End time")]
    slot_duration_minutes: Annotated[int, Field(description="Slot duration in minutes")]
    is_active: Annotated[bool, Field(description="Is slot active")]

    model_config = ConfigDict(from_attributes=True)
