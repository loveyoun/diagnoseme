from datetime import datetime
from enum import StrEnum

from tortoise import fields

from app.models.commonmodel import CommonModel


class SlotType(StrEnum):
    NORMAL = "normal"
    HOT = "hot"


class Slot(CommonModel):
    id: int = fields.BigIntField(primary_key=True)

    hospital: int = fields.ForeignKeyField(
        "models.Hospital",
        related_name="appointment_slots",
        on_delete=fields.RESTRICT)
    doctor: int | None = fields.ForeignKeyField(
        "models.Doctor",
        null=True,
        default=None,
        related_name="appointment_slots",
        on_delete=fields.SET_NULL)
    type: SlotType = fields.CharEnumField(enum_type=SlotType, default=SlotType.NORMAL)

    capacity: int = fields.IntField(default=1)
    remains: int = fields.IntField(default=1)

    start_at: datetime = fields.DatetimeField()
    end_at: datetime = fields.DatetimeField()
    slot_duration_minutes: int = fields.IntField(default=30)
    is_active: bool = fields.BooleanField(default=True)

    class Meta:
        table = "appointment_slots"
        indexes = (
            # ("hospital", "start_at", "end_at"),
            # ("hospital", "doctor", "start_at", "end_at"),
            ("hospital", "is_active"),  # 예약 가능 슬롯 조회
            ("type",),  # normal/hot 필터링용
        )
