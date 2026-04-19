from tortoise import fields

from app.models import User
from app.models.commonmodel import CommonModel


class Hospital(CommonModel):
    id: int = fields.BigIntField(primary_key=True)
    name: str = fields.CharField(max_length=20)
    address: str = fields.CharField(max_length=255)
    phone_number: str = fields.CharField(max_length=15)
    is_active: bool = fields.BooleanField(default=True)

    class Meta:
        table = "hospitals"


class Doctor(CommonModel):
    id: int = fields.BigIntField(primary_key=True)
    hospital: fields.ForeignKeyRelation[Hospital] = fields.ForeignKeyField(
        "models.Hospital",
        related_name="doctors",
        on_delete=fields.RESTRICT)
    name: str = fields.CharField(max_length=10)
    specialty: str | None = fields.CharField(max_length=30, null=True, default=True)
    is_active: bool = fields.BooleanField(default=True)

    hospital_id: int

    class Meta:
        table = "doctors"


class UserDoctor(CommonModel):
    """User ↔ Doctor 다대다"""
    id: int = fields.BigIntField(primary_key=True)

    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User",
        related_name="user_doctors",
        on_delete=fields.CASCADE,
    )
    doctor: fields.ForeignKeyRelation[Doctor] = fields.ForeignKeyField(
        "models.Doctor",
        related_name="user_doctors",
        on_delete=fields.CASCADE,
    )

    is_active: bool = fields.BooleanField(default=True)

    user_id: int
    doctor_id: int

    class Meta:
        table = "user_doctors"
        unique_together = (("user_id", "doctor_id"),)  # 중복 등록 방지
