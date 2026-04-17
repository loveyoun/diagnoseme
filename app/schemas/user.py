from typing import Annotated

from pydantic import BaseModel, EmailStr, Field

from app.models.user import Gender
from app.schemas.frozen_config import FROZEN_RESPONSE_CONFIG, FROZEN_CONFIG


class UserUpdateRequest(BaseModel):
    email: Annotated[EmailStr, Field(default=None, max_lenth=255, description="Unique email. For login.")]
    password: Annotated[str, Field(default=None, min_length=8, max_length=20, description="Password. ge(8), le(20)")]
    name: Annotated[str, Field(default=None)]
    nickname: Annotated[str, Field(default=None, description="Unique nickname")]
    phone_number: Annotated[str | None, Field(default=None, pattern=r"^\d{10,15}$")]
    gender: Annotated[Gender, Field(default=Gender.U)]
    # birthday: Annotated[datetime | None, Field(default=None)]
    birthday: Annotated[str, Field(default=None, pattern=r"^\d{2}-\d{2}$", description="Birthday (MM-DD)")]
    birthyear: Annotated[str, Field(default=None, pattern=r"^\d{4}$", description="Birth year (YYYY)")]
    profile_image: Annotated[str | None, Field(default=None, description="Profile image URL")]
    role: Annotated[str, Field(default=None, description="User role name")]

    model_config = FROZEN_CONFIG


class UserRoleResponse(BaseModel):
    id: int

    # validation/meta
    code: Annotated[str, Field(description="Role 이름")]

    model_config = FROZEN_RESPONSE_CONFIG


class UserResponse(BaseModel):
    id: int
    email: Annotated[EmailStr, Field(max_lenth=255, description="Unique email. For login.")]
    name: str
    nickname: Annotated[str, Field(description="Unique nickname")]

    # json: null
    phone_number: Annotated[str | None, Field(default=None)]
    gender: Annotated[Gender, Field(description="M/F/U")]
    # birthday: Annotated[datetime | None, Field(default=None)]
    birthday: Annotated[str, Field(description="Birthday (MM-DD)")]
    birthyear: Annotated[str, Field(description="Birth year (YYYY)")]
    profile_image: Annotated[str | None, Field(default=None, description="Profile image URL")]

    role: Annotated[UserRoleResponse, Field(description="User role id, name")]
    is_active: bool

    model_config = FROZEN_RESPONSE_CONFIG
