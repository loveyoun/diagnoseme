from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from tortoise import fields
from tortoise.exceptions import IntegrityError
from tortoise.transactions import in_transaction, F

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
                                                          default=IdempotencyStatus.SUCCESS)

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

    @classmethod
    async def create_appointment(
            cls, idem_key: str, user_id: int, slot_id: int, memo: str | None
    ) -> Appointment:
        # 1. 트랜잭션 시작
        async with in_transaction() as conn:
            # [Step 1] 원자적 슬롯 차감 (SQL: UPDATE ... WHERE remains > 0)
            # update()는 영향받은 로우의 개수를 반환합니다.
            updated_count = await Slot.filter(
                id=slot_id,
                remains__gt=0,
                is_active=True
            ).using_db(conn).update(remains=F("remains") - 1)

            if updated_count == 0:
                # 슬롯이 없거나, 비활성이거나, 잔여량이 없는 경우
                raise RuntimeError(f"Slot {slot_id} is unavailable or sold out")

            # [Step 2] 슬롯 정보 가져오기 (예약 생성을 위한 메타데이터)
            slot = await Slot.get(id=slot_id, using_db=conn)

            sql = """
                  UPDATE slots
                  SET remains = remains - 1
                  WHERE id = $1 \
                    AND remains > 0 \
                    AND is_active = True RETURNING id, hospital_id, start_at, end_at; \
                  """
            result = await conn.execute_query_dict(sql, [slot_id])

            if not result:
                raise ValueError("슬롯이 없거나 잔여 재고가 없습니다.")
            slot_data=result[0]
            try:
                # [Step 3] 예약 생성 (Unique Constraint: user_id + slot_id 또는 idem_key)
                # idem_key가 DB 수준의 Unique 제약조건으로 걸려 있어야 합니다.
                appointment = await Appointment.create(
                    idem_key=idem_key,
                    idem_status=IdempotencyStatus.SUCCESS,
                    user_id=user_id,
                    slot_id=slot_id,
                    hospital_id=slot.hospital_id,
                    start_at=slot.start_at,
                    end_at=slot.end_at,
                    status=AppointmentStatus.CONFIRMED,
                    memo=memo,
                    using_db=conn
                )
                return appointment

            except IntegrityError:
                # 중복 예약(idem_key 충돌 등) 발생 시 롤백됨 (수량은 트랜잭션에 의해 자동 복구)
                # 만약 "ON CONFLICT DO NOTHING"처럼 처리하고 싶다면 여기서 기존 예약을 조회해 반환
                existing = await Appointment.get_or_none(idem_key=idem_key, using_db=conn)
                if existing:
                    return existing
                raise RuntimeError("Concurrency conflict or Duplicate request")
