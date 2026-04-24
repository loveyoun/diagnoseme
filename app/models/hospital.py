from tortoise import fields

from app.models.commonmodel import CommonModel
from app.models.relations import RequestStatus


class Hospital(CommonModel):
    id: int = fields.BigIntField(primary_key=True)
    name: str = fields.CharField(max_length=20)
    address: str = fields.CharField(max_length=255)
    phone_number: str = fields.CharField(max_length=15)
    is_active: bool = fields.BooleanField(default=False)  # 운영 여부

    status: RequestStatus = fields.CharEnumField(enum_type=RequestStatus,
                                                 default=RequestStatus.PENDING)

    class Meta:
        table = "hospitals"
