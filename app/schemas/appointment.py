from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from app.models.appointment import AppointmentStatus, IdempotentStatus
from app.schemas.frozen_config import FROZEN_RESPONSE_CONFIG


class PollingRequest(BaseModel):
    slot_id: int
    idempotency_key: Annotated[str, Field(max_length=255, description="Idempotency key")]


class AppointmentRequest(PollingRequest):
    memo: Annotated[str | None, Field(default=None, description="Memo")]


class AppointmentCancelRequest(BaseModel):
    cancel_reason_id: Annotated[int | None, Field(default=None, description="Cancel reason ID")]


class AppointmentResponse(BaseModel):
    id: int
    idempotency_key: str
    idempotent_status: IdempotentStatus

    slot_id: int
    user_id: int
    hospital_id: int

    start_at: datetime
    end_at: datetime
    status: AppointmentStatus

    memo: str | None
    cancelled_at: datetime | None
    cancelled_by: int | None

    model_config = FROZEN_RESPONSE_CONFIG
