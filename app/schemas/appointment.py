from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.appointment import AppointmentStatus, IdempotentStatus
from app.schemas.frozen_config import FROZEN_RESPONSE_CONFIG


class AppointmentBase(BaseModel):
    slot_id: int
    memo: Annotated[str | None, Field(default=None, description="Memo")]


class AppointmentCreate(AppointmentBase):
    idempotency_key: Annotated[UUID, Field(description="Idempotency key")]


class AppointmentCancel(BaseModel):
    cancel_reason_id: Annotated[int | None, Field(default=None, description="Cancel reason ID")]


class AppointmentResponse(BaseModel):
    id: int
    idempotency_key: Annotated[str, Field(max_lenth=255, description="Idempotency key. Unique")]
    idempotent_status: Annotated[IdempotentStatus, Field(description="Idempotent status")]

    slot_id: int
    user_id: int
    hospital_id: int

    start_at: datetime
    end_at: datetime
    status: Annotated[AppointmentStatus, Field(description="Appointment status")]

    memo: Annotated[str | None, Field(default=None, description="Memo")]
    cancelled_at: Annotated[datetime | None, Field(default=None)]
    cancelled_by: Annotated[int | None, Field(default=None)]

    model_config = FROZEN_RESPONSE_CONFIG
