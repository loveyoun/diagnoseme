from datetime import datetime
from enum import StrEnum
from uuid import UUID

from tortoise import fields, models

from app.models.common import Common


class AppointmentStatus(StrEnum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    COMPLETED = "completed"


class CancelReason(models.Model):
    id: int = fields.SmallIntField(primary_key=True)
    code: str = fields.CharField(max_length=50, unique=True)

    class Meta:
        table = "cancel_reasons"


class Appointment(Common):
    id: int = fields.BigIntField(primary_key=True)
    idempotency_key: UUID = fields.UUIDField(unique=True)

    slot: int = fields.ForeignKeyField("models.AppointmentSlot", related_name="appointments", on_delete=fields.RESTRICT)
    user: int = fields.ForeignKeyField("models.User", related_name="appointments", on_delete=fields.RESTRICT)

    hospital: int = fields.ForeignKeyField("models.Hospital", on_delete=fields.RESTRICT)
    start_at: datetime = fields.DatetimeField()
    end_at: datetime = fields.DatetimeField()

    status: AppointmentStatus = fields.CharEnumField(enum_type=AppointmentStatus, default=AppointmentStatus.CONFIRMED)

    memo: str | None = fields.TextField(null=True)

    cancelled_at: datetime | None = fields.DatetimeField(null=True)
    cancelled_by: int | None = fields.ForeignKeyField("models.User", related_name="cancelled_appointments",
                                                      on_delete=fields.RESTRICT, null=True)
    cancel_reason: int | None = fields.ForeignKeyField("models.CancelReason", on_delete=fields.SET_NULL, null=True)

    class Meta:
        table = "appointments"
        unique_together = (("user", "slot"),)  # 동일 유저 동일 슬롯 중복 방지
        indexes = (
            ("user", "status"),  # 내 예약 목록 조회
            ("hospital", "start_at"),  # 병원별 일자별 예약자 명단용
            ("slot", "status"),  # 슬롯 기준 예약 조회
        )


