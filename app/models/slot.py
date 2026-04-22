from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from tortoise import fields

from app.models import Hospital, DoctorProfile
from app.models.commonmodel import CommonModel
from app.schemas.slot import SlotRequest


class SlotType(StrEnum):
    NORMAL = "normal"
    HOT = "hot"


class Slot(CommonModel):
    id: int = fields.BigIntField(primary_key=True)

    hospital: fields.ForeignKeyRelation[Hospital] = fields.ForeignKeyField(
        "models.Hospital",
        related_name="slots",
        on_delete=fields.RESTRICT)
    doctor: fields.ForeignKeyRelation[DoctorProfile] | None = fields.ForeignKeyField(
        "models.Doctor",
        related_name="slots",
        on_delete=fields.SET_NULL,
        null=True,
        default=None,
    )
    type: SlotType = fields.CharEnumField(enum_type=SlotType, default=SlotType.NORMAL)

    capacity: int = fields.IntField(default=1)
    remains: int = fields.IntField(default=1)
    start_at: datetime = fields.DatetimeField()
    end_at: datetime = fields.DatetimeField()
    slot_duration_minutes: int = fields.IntField(default=30)

    # 기본은 deactivated
    is_active: bool = fields.BooleanField(default=False)

    hospital_id: int
    doctor_id: int

    class Meta:
        table = "slots"
        indexes = (
            # partial unique index
            # ("hospital", "start_at", "end_at"),
            # ("hospital", "doctor", "start_at", "end_at"),
            ("hospital", "is_active"),  # 병원 별 예약 가능 슬롯 조회
            "type",  # normal/hot 필터링용
        )

    @classmethod
    async def get_by_id(cls, slot_id: int) -> Slot | None:
        return await cls.get_or_none(id=slot_id)

    @classmethod
    async def create_slot(cls, slot_req: SlotRequest) -> Slot:
        # 딕셔너리로 변환
        # Pydantic default != DB default
        data = slot_req.model_dump(exclude_unset=True)

        # 필요한 경우 특정 값 가공
        # data['doctor_id'] = data.get('doctor_id') or None
        data['is_active'] = True

        return await cls.create(**data)

    @classmethod
    async def activate(cls, slot_id: int) -> None:
        await cls.filter(id=slot_id).update(is_active=True)
