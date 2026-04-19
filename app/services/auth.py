from datetime import datetime, timezone

from fastapi import HTTPException
from passlib.context import CryptContext
from tortoise.exceptions import IntegrityError
from tortoise.transactions import atomic

from app.core import config, password_hasher
from app.core.redis import redis_client  # access token blacklist
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User, UserRole
from app.schemas.auth import TokenResponse, SignInRequest, SignUpRequest

pwd_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    @staticmethod
    @atomic  # in_transaction()
    async def service_auth_sign_up(user_data: SignUpRequest) -> User:
        if await User.exists(email=user_data.email):
            raise HTTPException(status_code=400, detail=f"Email {user_data.email} already registered")
        if await User.exists(nickname=user_data.nickname):
            raise HTTPException(status_code=400, detail=f"Nickname {user_data.nickname} already taken")

        # ORM instance UserRole
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
            raise HTTPException(
                status_code=400,
                detail=f"Email{user_data.email} or Nickname{user_data.nickname} already exists or User role{user_data.role} deleted")

    @staticmethod
    async def signin(user_data: SignInRequest) -> TokenResponse:
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

    @staticmethod
    def get_password_hash(password: str) -> str:
        return password_hasher.hash(password)
        # return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return password_hasher.verify(plain_password, hashed_password)
        # return pwd_context.verify(plain_password, hashed_password)

    async def authenticate(self, email: str, password: str) -> User | None:
        # user = await self.get_by_email(email)
        user = User()
        if not user:
            password_hasher.verify_dummy(password)
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user

    async def authenticate_with_rehash(
            self,
            email: str,
            password: str,
    ) -> User | None:
        user = await self.get_by_email(email)

        if not user:
            password_hasher.verify_dummy(password)
            return None
        if not self.verify_password(password, user):
            return None
        # 보안 정책 업그레이드 체크
        if password_hasher.check_needs_rehash(user.hashed_password):
            user.hashed_password = password_hasher.hash(password)
        return user
