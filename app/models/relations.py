from __future__ import annotations

from enum import StrEnum

from tortoise import fields

from app.models import User, Hospital, UserRole
from app.models.commonmodel import CommonModel


class RequestStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class DoctorProfile(CommonModel):
    id: int = fields.BigIntField(primary_key=True)

    # User 1명당 Doctor 프로필은 딱 1개만 존재해야 함
    user: fields.OneToOneRelation[User] = fields.OneToOneField(
        "models.User",
        related_name="doctor_profile",
        on_delete=fields.CASCADE,
        # unique=True,
    )
    hospital: fields.ForeignKeyRelation[Hospital] | None = fields.ForeignKeyField(
        "models.Hospital",
        related_name="doctors",
        on_delete=fields.SET_NULL,
        null=True,
        default=None,
    )

    license_number: str = fields.CharField(max_length=15)
    specialty: str | None = fields.CharField(max_length=20, null=True, default=True)
    is_active: bool = fields.BooleanField(default=False)  # 활동 여부

    status: RequestStatus = fields.CharEnumField(enum_type=RequestStatus,
                                                 default=RequestStatus.PENDING)

    user_id: int
    hospital_id: int | None

    class Meta:
        table = "doctors"


class UserHospital(CommonModel):
    id: int = fields.BigIntField(primary_key=True)

    # faculty
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

    user_id: int
    hospital_id: int

    class Meta:
        table = "user_hospitals"
        unique_together = (("user", "hospital"),)


class RoleRequest(CommonModel):
    id: int = fields.BigIntField(primary_key=True)

    # User 당 Role 1개
    user: fields.OneToOneRelation[User] = fields.OneToOneField(
        "models.User",
        related_name="role_request",
        on_delete=fields.CASCADE,
    )
    role: fields.ForeignKeyRelation[UserRole] = fields.ForeignKeyField(
        "models.UserRole",
        related_name="role_requests",
        on_delete=fields.CASCADE,
    )
    hospital: fields.ForeignKeyRelation[Hospital] = fields.ForeignKeyField(
        "models.Hospital",
        related_name="role_requests",
        on_delete=fields.CASCADE,
    )
    status: RequestStatus = fields.CharEnumField(enum_type=RequestStatus,
                                                 default=RequestStatus.PENDING)

    user_id: int
    role_id: int
    hospital_id: int

    class Meta:
        table = "role_requests"
        indexes = ("status",)


class HospitalRequest(CommonModel):
    id: int = fields.BigIntField(primary_key=True)

    hospital: fields.OneToOneRelation[Hospital] = fields.OneToOneRelation(
        "models.Hospital",
        related_name="hospital_request",
        on_delete=fields.CASCADE,
    )
    status: RequestStatus = fields.CharEnumField(enum_type=RequestStatus,
                                                 default=RequestStatus.PENDING)

    hospital_id: int

    class Meta:
        table = "hospital_requests"
        indexes = ("status",)
