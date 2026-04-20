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


class DoctorProfile(CommonModel):
    id: int = fields.BigIntField(primary_key=True)

    # User 1명당 Doctor 프로필은 딱 1개만 존재해야 함
    # Unique Constraint
    user: fields.OneToOneRelation[User] | None = fields.OneToOneField(
        "models.User",
        related_name="doctor_profile",
        on_delete=fields.SET_NULL,
        null=True,
        default=None
    )
    hospital: fields.ForeignKeyRelation[Hospital] | None = fields.ForeignKeyField(
        "models.Hospital",
        related_name="doctors",
        on_delete=fields.SET_NULL,
        null=True,
        default=None
    )

    license_number: str = fields.CharField(max_length=15)
    specialty: str | None = fields.CharField(max_length=20, null=True, default=True)
    approved: bool = fields.BooleanField(default=True)

    user_id: int
    hospital_id: int

    class Meta:
        table = "doctors"


class UserHospital(CommonModel):
    id: int = fields.BigIntField(primary_key=True)

    user: fields.OneToOneRelation[User] = fields.OneToOneField(
        "models.User",
        related_name="user_hospital",
        on_delete=fields.CASCADE,
    )
    hospital: fields.ForeignKeyRelation[Hospital] = fields.ForeignKeyField(
        "models.Hospital",
        related_name="user_hospitals",
        on_delete=fields.CASCADE,
    )

    approved: bool = fields.BooleanField(default=True)

    user_id: int
    hospital_id: int

    class Meta:
        table = "user_hospitals"
