from typing import Annotated

from pydantic import BaseModel, EmailStr, Field

from app.models.user import Gender
from app.schemas.frozen_config import FROZEN_CONFIG, FROZEN_RESPONSE_CONFIG


class SignUpRequest(BaseModel):
    email: Annotated[EmailStr, Field(..., max_lenth=255, description="Unique email. For login.")]
    password: Annotated[str, Field(min_length=8, max_length=20, description="Password. ge(8), le(20)")]
    name: Annotated[str, Field(max_length=10)]
    nickname: Annotated[str, Field(max_length=10, description="Unique nickname")]
    phone_number: Annotated[str | None, Field(default=None, pattern=r"^\d{10,15}$")]
    gender: Annotated[Gender, Field(default=Gender.U)]
    # birthday: Annotated[datetime | None, Field(default=None)]
    birthday: Annotated[str, Field(pattern=r"^\d{2}-\d{2}$", description="Birthday (MM-DD)")]
    birthyear: Annotated[str, Field(pattern=r"^\d{4}$", description="Birth year (YYYY)")]
    profile_image: Annotated[str | None, Field(default=None, description="Profile image URL")]
    role: Annotated[str, Field(description="User role name")]

    model_config = FROZEN_CONFIG


class SignInRequest(BaseModel):
    email: str
    password: str

    model_config = FROZEN_CONFIG


class TokenResponse(BaseModel):
    """ 로그인 응답 """
    access_token: Annotated[str, Field(description="Access token")]
    token_type: Annotated[str, Field(default="bearer", description="Token type")]

    model_config = FROZEN_RESPONSE_CONFIG
