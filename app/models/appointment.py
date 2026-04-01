from enum import StrEnum
from tortoise import fields, models
from app.models.common import Common


class AppointmentStatus(StrEnum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    COMPLETED = "completed"


class CancelReason(models.Model):
    id = fields.SmallIntField(primary_key=True)
    code = fields.CharField(max_length=50, unique=True)

    class Meta:
        table = "cancel_reasons"


class Appointment(Common):
    id = fields.BigIntField(primary_key=True)
    idempotency_key = fields.UUIDField(unique=True)

    slot = fields.ForeignKeyField("models.AppointmentSlot", related_name="appointments", on_delete=fields.RESTRICT)
    user = fields.ForeignKeyField("models.User", related_name="appointments", on_delete=fields.RESTRICT)

    hospital = fields.ForeignKeyField("models.Hospital", on_delete=fields.RESTRICT)
    start_at = fields.DatetimeField()
    end_at = fields.DatetimeField()

    status = fields.CharEnumField(enum_type=AppointmentStatus, default=AppointmentStatus.CONFIRMED)

    memo = fields.TextField(null=True)

    cancelled_at = fields.DatetimeField(null=True)
    cancelled_by = fields.ForeignKeyField("models.User", related_name="cancelled_appointments", on_delete=fields.RESTRICT, null=True)
    cancel_reason = fields.ForeignKeyField("models.CancelReason", on_delete=fields.SET_NULL, null=True)

    class Meta:
        table = "appointments"
        unique_together = (("user", "slot"),)  # 동일 유저 동일 슬롯 중복 방지
        indexes = (
            ("user", "status"),  # 내 예약 목록 조회
            ("hospital", "start_at"),  # 병원별 일자별 예약자 명단용
            ("slot", "status"),  # 슬롯 기준 예약 조회
        )
