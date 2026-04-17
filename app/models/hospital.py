from tortoise import fields

from app.models.commonmodel import CommonModel


class Hospital(CommonModel):
    id: int = fields.BigIntField(primary_key=True)
    name: str = fields.CharField(max_length=50)
    address: str = fields.CharField(max_length=255)
    phone_number: str = fields.CharField(max_length=20)
    is_active: bool = fields.BooleanField(default=True)

    class Meta:
        table = "hospitals"


class Doctor(CommonModel):
    id: int = fields.BigIntField(primary_key=True)
    hospital: int = fields.ForeignKeyField(
        "models.Hospital",
        related_name="doctors",
        on_delete=fields.RESTRICT)
    name: str = fields.CharField(max_length=10)
    specialty: str | None = fields.CharField(max_length=30, null=True, default=True)
    is_active: bool = fields.BooleanField(default=True)

    hospital_id: int

    class Meta:
        table = "doctors"
