from datetime import datetime
from enum import StrEnum

from tortoise import fields, models

from app.models.common import Common


class Gender(StrEnum):
    M = "M"
    F = "F"
    U = "U"  # unknown


class UserRole(models.Model):
    id: int = fields.SmallIntField(primary_key=True)
    code: str = fields.CharField(max_length=20, unique=True)

    class Meta:
        table = "user_roles"


class User(Common):
    id: int = fields.BigIntField(primary_key=True)
    hashed_password: str = fields.CharField(max_length=128)
    email: str = fields.CharField(max_length=255, unique=True)
    phone_number: str | None = fields.CharField(max_length=20, null=True)  # nullable

    name: str = fields.CharField(max_length=30)
    nickname: str = fields.CharField(max_length=10, unique=True)
    gender: Gender = fields.CharEnumField(enum_type=Gender, default=Gender.U)  # default
    birthday: str = fields.CharField(max_length=5)  # MM-DD
    birthyear: str = fields.CharField(max_length=4)  # YYYY
    profile_image: str | None = fields.CharField(max_length=255, null=True)  # nullable

    role: int = fields.ForeignKeyField("models.UserRole", on_delete=fields.RESTRICT)
    is_active: bool = fields.BooleanField(default=True)  # default
    last_login_at: datetime | None = fields.DatetimeField(null=True)

    class Meta:
        table = "users"
