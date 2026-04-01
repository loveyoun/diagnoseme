from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from app.models.appointment import AppointmentStatus


class AppointmentBase(BaseModel):
    slot_id: int
    memo: str | None = None


class AppointmentCreate(AppointmentBase):
    idempotency_key: UUID


class AppointmentResponse(BaseModel):
    id: int
    idempotency_key: UUID
    slot_id: int
    user_id: int
    hospital_id: int
    start_at: datetime
    end_at: datetime
    status: AppointmentStatus
    memo: str | None

    model_config = ConfigDict(from_attributes=True)


class AppointmentCancel(BaseModel):
    cancel_reason_id: int | None = None
