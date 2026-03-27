from pydantic import BaseModel
from typing import Optional

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: int
    naver_id: Optional[str]
    email: Optional[str]
    nickname: Optional[str]
    profile_image: Optional[str]

    class Config:
        from_attributes = True
