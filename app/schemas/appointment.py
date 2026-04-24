from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from app.models.appointment import AppointmentStatus, IdempotencyStatus
from app.schemas.frozen_config import FROZEN_RESPONSE_CONFIG, FROZEN_CONFIG


class PollingRequest(BaseModel):
    idem_key: Annotated[str, Field(max_length=255, description="Idempotency key")]

    model_config = FROZEN_CONFIG


class AppointmentRequest(PollingRequest):
    slot_id: int
    memo: Annotated[str | None, Field(default=None, description="Memo")]

    model_config = FROZEN_CONFIG


class AppointmentCancelRequest(BaseModel):
    cancel_reason_id: Annotated[int | None, Field(default=None, description="Cancel reason ID")]
    cancel_reason_code: Annotated[str, Field(max_length=20, description="Cancel reason code")]

    model_config = FROZEN_CONFIG


class CancelReasonResponse(BaseModel):
    id: int
    code: str

    model_config = FROZEN_RESPONSE_CONFIG


class AppointmentResponse(BaseModel):
    id: int
    idem_key: str
    idem_status: IdempotencyStatus
    user_id: int
    slot_id: int

    hospital_id: int
    start_at: datetime
    end_at: datetime
    status: AppointmentStatus
    memo: str | None

    cancelled_at: datetime | None
    cancelled_by: int | None
    cancel_reason: CancelReasonResponse | None

    model_config = FROZEN_RESPONSE_CONFIG
