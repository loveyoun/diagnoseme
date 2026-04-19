from typing import Annotated

from pydantic import BaseModel, EmailStr, Field

from app.models.user import Gender
from app.schemas.frozen_config import FROZEN_RESPONSE_CONFIG, FROZEN_CONFIG


class UserUpdateRequest(BaseModel):
    email: Annotated[EmailStr | None, Field(default=None, max_lenth=255, description="Unique email. For login.")]
    password: Annotated[
        str | None, Field(default=None, min_length=8, max_length=20, description="Password. ge(8), le(20)")]
    name: Annotated[str | None, Field(default=None, max_length=10)]
    nickname: Annotated[str | None, Field(default=None, max_length=10, description="Unique nickname")]
    phone_number: Annotated[str | None, Field(default=None, pattern=r"^\d{10,15}$")]
    gender: Annotated[Gender | None, Field(default=None)]
    # birthday: Annotated[datetime | None, Field(default=None)]
    birthday: Annotated[str | None, Field(default=None, pattern=r"^\d{2}-\d{2}$", description="Birthday (MM-DD)")]
    birthyear: Annotated[str | None, Field(default=None, pattern=r"^\d{4}$", description="Birth year (YYYY)")]
    profile_image: Annotated[str | None, Field(default=None, description="Profile image URL")]
    role: Annotated[str | None, Field(default=None, description="User role name")]

    model_config = FROZEN_CONFIG


class UserRoleResponse(BaseModel):
    id: int

    # validation/meta
    code: Annotated[str, Field(description="Role 이름")]

    model_config = FROZEN_RESPONSE_CONFIG


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: str
    nickname: str

    # json: null
    phone_number: str | None
    gender: Gender
    # birthday: datetime
    birthday: Annotated[str, Field(description="Birthday (MM-DD)")]
    birthyear: Annotated[str, Field(description="Birth year (YYYY)")]
    profile_image: str | None

    role: Annotated[UserRoleResponse, Field(description="User role id, name")]
    is_active: bool

    model_config = FROZEN_RESPONSE_CONFIG
