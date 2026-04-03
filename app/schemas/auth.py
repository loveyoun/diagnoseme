from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models.user import Gender


class UserSignin(BaseModel):
    """ 로그인할 때 가져오는 정보 """
    email: Annotated[str, Field(description="Email address")]
    password: Annotated[str, Field(description="Raw password")]


class TokenResponse(BaseModel):
    """ 로그인 응답 """
    access_token: Annotated[str, Field(description="Access token")]
    token_type: Annotated[str, Field(default="bearer", description="Token type")]


class SignUpRequest(BaseModel):
    """ 회원가입할 때 """
    password: Annotated[str, Field(..., min_length=8, description="Password")]
    email: Annotated[EmailStr, Field(description="Email address")]
    phone_number: Annotated[str | None, Field(default=None, pattern=r"^\d{10,15}$", description="Phone number")]
    name: Annotated[str, Field(description="Name")]
    nickname: Annotated[str, Field(description="Nickname")]
    gender: Annotated[Gender | None, Field(default=Gender.U, description="Gender")]
    birthday: Annotated[str, Field(..., pattern=r"^\d{2}-\d{2}$", description="Birthday (MM-DD)")]
    birthyear: Annotated[str, Field(..., pattern=r"^\d{4}$", description="Birth year (YYYY)")]
    profile_image: Annotated[str | None, Field(default=None, description="Profile image URL")]
    role: Annotated[str, Field(description="Role code")]
