from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.appointment import AppointmentStatus


class AppointmentBase(BaseModel):
    slot_id: Annotated[int, Field(description="Slot ID")]
    memo: Annotated[str | None, Field(default=None, description="Memo")]


class AppointmentCreate(AppointmentBase):
    idempotency_key: Annotated[UUID, Field(description="Idempotency key")]


class AppointmentResponse(BaseModel):
    id: Annotated[int, Field(description="Appointment ID")]
    idempotency_key: Annotated[UUID, Field(description="Idempotency key")]
    slot_id: Annotated[int, Field(description="Slot ID")]
    user_id: Annotated[int, Field(description="User ID")]
    hospital_id: Annotated[int, Field(description="Hospital ID")]
    start_at: Annotated[datetime, Field(description="Start time")]
    end_at: Annotated[datetime, Field(description="End time")]
    status: Annotated[AppointmentStatus, Field(description="Appointment status")]
    memo: Annotated[str | None, Field(default=None, description="Memo")]

    model_config = ConfigDict(from_attributes=True)


class AppointmentCancel(BaseModel):
    cancel_reason_id: Annotated[int | None, Field(default=None, description="Cancel reason ID")]
