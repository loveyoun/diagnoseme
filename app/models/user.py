from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from tortoise import fields

from app.models.commonmodel import CommonModel


class Gender(StrEnum):
    M = "M"
    F = "F"
    U = "U"  # unknown


class UserRole(CommonModel):
    id: int = fields.SmallIntField(primary_key=True)

    # user(가입할 때), faculty/doctor(신청), admin
    code: str = fields.CharField(max_length=20, unique=True)

    class Meta:
        table = "user_roles"


class User(CommonModel):
    id: int = fields.BigIntField(primary_key=True)
    email: str = fields.CharField(max_length=255, unique=True)
    hashed_password: str = fields.CharField(max_length=255)  # Argon2id

    name: str = fields.CharField(max_length=10)
    nickname: str = fields.CharField(max_length=10, unique=True)

    # nullable. "" != NULL
    phone_number: str | None = fields.CharField(max_length=15, null=True, default=None)
    gender: Gender = fields.CharEnumField(enum_type=Gender, default=Gender.U)  # default
    # birthday: datetime = fields.DatetimeField()
    birthday: str = fields.CharField(max_length=5)  # MM-DD
    birthyear: str = fields.CharField(max_length=4)  # YYYY
    profile_image: str | None = fields.CharField(max_length=255, null=True, default=None)  # nullable

    role: fields.ForeignKeyRelation[UserRole] = fields.ForeignKeyField(
        "models.UserRole",
        on_delete=fields.RESTRICT)
    is_active: bool = fields.BooleanField(default=True)  # default
    last_login_at: datetime | None = fields.DatetimeField(null=True, default=None)  # nullable

    role_id: int

    class Meta:
        table = "users"

    @classmethod
    async def get_by_id(cls, user_id: int) -> User | None:
        return await cls.get_or_none(id=user_id)  # .select_related("role")
