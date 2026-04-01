from tortoise import fields
from app.models.common import Common


class Hospital(Common):
    id = fields.BigIntField(primary_key=True)
    name = fields.CharField(max_length=50)
    address = fields.CharField(max_length=255)
    phone_number = fields.CharField(max_length=20)
    is_active = fields.BooleanField(default=True)

    class Meta:
        table = "hospitals"


class Doctor(Common):
    id = fields.BigIntField(primary_key=True)
    hospital = fields.ForeignKeyField("models.Hospital", related_name="doctors", on_delete=fields.RESTRICT)
    name = fields.CharField(max_length=30)
    specialty = fields.CharField(max_length=100, null=True)
    is_active = fields.BooleanField(default=True)

    class Meta:
        table = "doctors"
