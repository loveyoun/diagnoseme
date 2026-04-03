from tortoise import fields

from app.models.common import Common


class Hospital(Common):
    id: int = fields.BigIntField(primary_key=True)
    name: str = fields.CharField(max_length=50)
    address: str = fields.CharField(max_length=255)
    phone_number: str = fields.CharField(max_length=20)
    is_active: bool = fields.BooleanField(default=True)

    class Meta:
        table = "hospitals"


class Doctor(Common):
    id: int = fields.BigIntField(primary_key=True)
    hospital: int = fields.ForeignKeyField("models.Hospital", related_name="doctors", on_delete=fields.RESTRICT)
    name: str = fields.CharField(max_length=30)
    specialty: str | None = fields.CharField(max_length=100, null=True)
    is_active: bool = fields.BooleanField(default=True)

    class Meta:
        table = "doctors"
