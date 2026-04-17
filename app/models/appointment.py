from datetime import datetime
from enum import StrEnum

from tortoise import fields, models

from app.models.commonmodel import CommonModel


class AppointmentStatus(StrEnum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    COMPLETED = "completed"


class IdempotentStatus(StrEnum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class CancelReason(models.Model):
    id: int = fields.SmallIntField(primary_key=True)
    code: str = fields.CharField(max_length=50, unique=True)

    class Meta:
        table = "cancel_reasons"


class Appointment(CommonModel):
    id: int = fields.BigIntField(primary_key=True)
    idempotent_key: str = fields.CharField(max_length=255, unique=True)
    idempotent_status: IdempotentStatus = fields.CharEnumField(enum_type=IdempotentStatus,
                                                                default=IdempotentStatus.PENDING)

    slot: int = fields.ForeignKeyField(
        "models.AppointmentSlot",
        related_name="appointments",
        on_delete=fields.RESTRICT)
    user: int = fields.ForeignKeyField(
        "models.User",
        related_name="appointments",
        on_delete=fields.RESTRICT)
    hospital: int = fields.ForeignKeyField(
        "models.Hospital",
        related_name="appointments",
        on_delete=fields.RESTRICT)

    start_at: datetime = fields.DatetimeField()
    end_at: datetime = fields.DatetimeField()
    status: AppointmentStatus = fields.CharEnumField(enum_type=AppointmentStatus,
                                                     default=AppointmentStatus.CONFIRMED)

    memo: str | None = fields.TextField(null=True, default=None)
    cancelled_at: datetime | None = fields.DatetimeField(null=True, default=None)
    cancelled_by: int | None = fields.ForeignKeyField(
        "models.User",
        related_name="cancelled_appointments",
        on_delete=fields.RESTRICT,
        null=True,
        default=None)
    cancel_reason: int | None = fields.ForeignKeyField(
        "models.CancelReason",
        on_delete=fields.SET_NULL,
        null=True,
        default=None)

    class Meta:
        table = "appointments"
        unique_together = (("user", "slot"),)  # 동일 유저 동일 슬롯 중복 방지
        indexes = (
            ("user", "status"),  # 내 예약 목록 조회
            ("hospital", "start_at"),  # 병원별 일자별 예약자 명단용
            ("slot", "status"),  # 슬롯 기준 예약 조회
        )
