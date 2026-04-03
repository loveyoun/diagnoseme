from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models.user import Gender


class UserRoleResponse(BaseModel):
    id: Annotated[int, Field(description="Role ID")]
    code: Annotated[str, Field(description="Role Code")]

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    """ 회원정보 응답 """
    id: Annotated[int, Field(description="User ID")]
    email: Annotated[str, Field(description="Email address")]
    phone_number: Annotated[str | None, Field(default=None, description="Phone number")]
    name: Annotated[str, Field(description="Name")]
    nickname: Annotated[str, Field(description="Nickname")]
    gender: Annotated[Gender, Field(description="Gender")]
    birthday: Annotated[str, Field(description="Birthday (MM-DD)")]
    birthyear: Annotated[str, Field(description="Birth year (YYYY)")]
    profile_image: Annotated[str | None, Field(default=None, description="Profile image URL")]
    role: Annotated[UserRoleResponse, Field(description="User role")]

    model_config = ConfigDict(from_attributes=True)


class UserUpdateRequest(BaseModel):
    """ 회원정보 수정 """
    password: Annotated[str | None, Field(..., min_length=8, description="Password")]
    email: Annotated[EmailStr | None, Field(default=None, description="Email address")]
    phone_number: Annotated[str | None, Field(default=None, pattern=r"^\d{10,15}$", description="Phone number")]
    name: Annotated[str | None, Field(default=None, description="Name")]
    nickname: Annotated[str | None, Field(default=None, description="Nickname")]
    gender: Annotated[Gender | None, Field(default=Gender.U, description="Gender")]
    birthday: Annotated[str | None, Field(..., pattern=r"^\d{2}-\d{2}$", description="Birthday (MM-DD)")]
    birthyear: Annotated[str | None, Field(..., pattern=r"^\d{4}$", description="Birth year (YYYY)")]
    profile_image: Annotated[str | None, Field(default=None, description="Profile image URL")]
    role: Annotated[str | None, Field(default=None, description="Role code")]
