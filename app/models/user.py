from enum import StrEnum
from tortoise import fields, models
from app.models.common import Common


class Gender(StrEnum):
    M = "M"
    F = "F"
    U = "U"


class UserRole(models.Model):
    id = fields.SmallIntField(primary_key=True)
    code = fields.CharField(max_length=20, unique=True)

    class Meta:
        table = "user_roles"


class User(Common):
    id = fields.BigIntField(primary_key=True)
    naver_id = fields.CharField(max_length=255, unique=True, null=True)
    hashed_password = fields.CharField(max_length=128, null=True)
    phone_number = fields.CharField(max_length=20, unique=True)

    name = fields.CharField(max_length=30)
    email = fields.CharField(max_length=254)
    nickname = fields.CharField(max_length=10, unique=True)
    gender = fields.CharEnumField(enum_type=Gender)
    birthday = fields.CharField(max_length=5)
    birthyear = fields.CharField(max_length=4)
    profile_image = fields.CharField(max_length=255, null=True)

    role = fields.ForeignKeyField("models.UserRole", on_delete=fields.RESTRICT)
    is_active = fields.BooleanField(default=True)
    last_login_at = fields.DatetimeField(null=True)

    class Meta:
        table = "users"
