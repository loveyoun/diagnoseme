from enum import StrEnum
from tortoise import fields
from app.models.common import Common


class SlotType(StrEnum):
    NORMAL = "normal"
    HOT = "hot"


class SlotTemplate(Common):
    id = fields.BigIntField(primary_key=True)
    type = fields.CharEnumField(enum_type=SlotType, default=SlotType.NORMAL)

    capacity = fields.IntField(default=1)
    remains = fields.IntField(default=1)

    start_at = fields.DatetimeField()
    end_at = fields.DatetimeField()
    slot_duration_minutes = fields.IntField(default=30)
    is_active = fields.BooleanField(default=False)

    class Meta:
        table = "slot_template"


class AppointmentSlot(Common):
    id = fields.BigIntField(primary_key=True)
    hospital = fields.ForeignKeyField("models.Hospital", related_name="appointment_slots", on_delete=fields.RESTRICT)
    doctor = fields.ForeignKeyField("models.Doctor", related_name="appointment_slots", on_delete=fields.SET_NULL, null=True)
    type = fields.CharEnumField(enum_type=SlotType, default=SlotType.NORMAL)

    capacity = fields.IntField(default=1)
    remains = fields.IntField(default=1)

    start_at = fields.DatetimeField()
    end_at = fields.DatetimeField()
    slot_duration_minutes = fields.IntField(default=30)
    is_active = fields.BooleanField(default=True)

    class Meta:
        table = "appointment_slots"
        # unique_together = (
        #     ("hospital", "start_at", "end_at"),
        #     ("hospital", "doctor", "start_at", "end_at")
        # )
        indexes = (
            ("hospital", "is_active"),  # 예약 가능 슬롯 조회
            ("type",),  # normal/hot 필터링용
        )
