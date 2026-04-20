from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from tortoise import fields

from app.models import Hospital, User, Slot
from app.models.commonmodel import CommonModel


class AppointmentStatus(StrEnum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    COMPLETED = "completed"


class IdempotencyStatus(StrEnum):
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"


class CancelReason(CommonModel):  # 이유1, 이유2, 기타추가
    id: int = fields.SmallIntField(primary_key=True)
    code: str = fields.CharField(max_length=20, unique=True)

    class Meta:
        table = "cancel_reasons"


class Appointment(CommonModel):
    id: int = fields.BigIntField(primary_key=True)
    idem_key: str = fields.CharField(max_length=255, unique=True)
    idem_status: IdempotencyStatus = fields.CharEnumField(enum_type=IdempotencyStatus,
                                                          default=IdempotencyStatus.PROCESSING)

    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User",
        related_name="appointments",
        on_delete=fields.RESTRICT)
    slot: fields.ForeignKeyRelation[Slot] = fields.ForeignKeyField(
        "models.Slot",
        related_name="appointments",
        on_delete=fields.RESTRICT)

    hospital: fields.ForeignKeyRelation[Hospital] = fields.ForeignKeyField(
        "models.Hospital",
        related_name="appointments",
        on_delete=fields.RESTRICT)
    start_at: datetime = fields.DatetimeField()
    end_at: datetime = fields.DatetimeField()
    status: AppointmentStatus = fields.CharEnumField(enum_type=AppointmentStatus,
                                                     default=AppointmentStatus.CONFIRMED)
    memo: str | None = fields.TextField(null=True, default=None)

    cancelled_at: datetime | None = fields.DatetimeField(null=True, default=None)
    cancelled_by: fields.ForeignKeyRelation[User] | None = fields.ForeignKeyField(
        "models.User",
        related_name="cancelled_appointments",
        on_delete=fields.SET_NULL,
        null=True,
        default=None)
    cancel_reason: fields.ForeignKeyRelation[CancelReason] | None = fields.ForeignKeyField(
        "models.CancelReason",
        related_name="cancelled_appointments",
        on_delete=fields.SET_NULL,
        null=True,
        default=None)

    user_id: int
    slot_id: int
    hospital_id: int
    cancelled_by_id: int
    cancel_reason_id: int

    class Meta:
        table = "appointments"
        unique_together = (("user", "slot"),)  # 동일 유저 동일 슬롯 중복 방지
        indexes = (
            # ("start_at", "end_at"),  # GiST
            ("user", "status"),  # 내 예약 목록 조회
            ("hospital", "start_at"),  # 병원별 일자별 예약자 명단용
            ("slot", "status"),  # 슬롯 기준 예약 조회
        )

    @classmethod
    async def get_by_idem_key(cls, idem_key: str) -> Appointment | None:
        return await cls.get_or_none(idem_key=idem_key)
