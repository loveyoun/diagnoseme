from tortoise import fields

from app.models.commonmodel import CommonModel


class Hospital(CommonModel):
    id: int = fields.BigIntField(primary_key=True)
    name: str = fields.CharField(max_length=20)
    address: str = fields.CharField(max_length=255)
    phone_number: str = fields.CharField(max_length=15)
    is_active: bool = fields.BooleanField(default=False)  # 운영 여부

    class Meta:
        table = "hospitals"
