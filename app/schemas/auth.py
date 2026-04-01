from pydantic import BaseModel, EmailStr, Field
from app.models.user import Gender

class TokenResponse(BaseModel):
    """ 로그인 응답 """
    access_token: str
    token_type: str = "bearer"

class UserSignup(BaseModel):
    phone_number: str = Field(..., pattern=r"^\d{10,15}$")
    password: str = Field(..., min_length=8)
    name: str
    email: EmailStr
    nickname: str
    gender: Gender
    birthday: str = Field(..., pattern=r"^\d{2}-\d{2}$") # MM-DD
    birthyear: str = Field(..., pattern=r"^\d{4}$")

class UserSignin(BaseModel):
    phone_number: str
    password: str

class UserResponse(BaseModel):
    id: int
    phone_number: str
    name: str
    email: str
    nickname: str
    gender: Gender

    class Config:
        from_attributes = True
