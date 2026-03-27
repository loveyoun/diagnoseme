from enum import StrEnum

from tortoise import fields, models


class Gender(StrEnum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    UNKNOWN = "UNKNOWN"


class User(models.Model):
    user_id = fields.BigIntField(primary_key=True)
    nickname = fields.CharField(max_length=10)
    email = fields.CharField(max_length=40, null=True)

    class Meta:
        table = "users"
