"""UserService — 순수 비즈니스 로직 담당.

서비스 레이어 규칙:
- commit() 호출 금지 → 트랜잭션은 라우터의 몫
- flush()로 DB에 전송만 → ID/서버 기본값을 받아오기 위함
- refresh()로 DB 상태 동기화 → server_default 값 반영
"""
from datetime import datetime, timezone

from fastapi import HTTPException
from tortoise.exceptions import IntegrityError
from tortoise.transactions import atomic

from app.core import config
from app.core.redis import redis_client  # access token blacklist
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User, UserRole
from app.schemas.auth import TokenResponse, UserSignin, SignUpRequest


class AuthService:
    @staticmethod
    @atomic()  # in_transaction()
    async def create(user_data: SignUpRequest) -> User:
        if await User.exists(email=user_data.email):
            raise HTTPException(status_code=400, detail="Email already registered")
        if await User.exists(nickname=user_data.nickname):
            raise HTTPException(status_code=400, detail="Nickname already taken")

        # ORM instance (UserRole)
        role, _ = await UserRole.get_or_create(code=user_data.role)

        try:
            user: User = await User.create(
                hashed_password=get_password_hash(user_data.password),
                email=user_data.email,
                phone_number=user_data.phone_number,
                name=user_data.name,
                nickname=user_data.nickname,
                gender=user_data.gender,
                birthday=user_data.birthday,
                birthyear=user_data.birthyear,
                role=role,
            )
            return user
        except IntegrityError:  # Unique Constraint
            # exists() 통과 후 race condition 방어
            raise HTTPException(status_code=400, detail="Already registered")

    @staticmethod
    async def signin(user_data: UserSignin) -> TokenResponse:
        user: User | None = await User.get_or_none(email=user_data.email)

        if not user or not user.hashed_password:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not verify_password(user_data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not user.is_active:
            raise HTTPException(status_code=401, detail="Account is disabled")

        user.last_login_at = datetime.now(timezone.utc)
        await user.save()

        access_token: str = create_access_token(data={"sub": str(user.id)})
        return TokenResponse(access_token=access_token)

    @staticmethod
    async def logout(token: str) -> None:
        await redis_client.set(
            f"blacklist:{token}",
            "1",
            ex=config.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
