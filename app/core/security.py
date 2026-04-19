from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from redis.asyncio import Redis

from app.core import config
from app.models.user import User
from pwdlib import PasswordHash

oauth2_scheme: OAuth2PasswordBearer = OAuth2PasswordBearer(tokenUrl="/auth/signin")

redis_client: Redis = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)


class PasswordHasher:
    def __init__(self) -> None:
        self._hasher = PasswordHash.recommended()

        # 타이밍 공격 방지용 더미 해시
        self._dummy_hash = self._hasher.hash("dummy-password-for-timing")

    def hash(self, plain_password: str) -> str:
        return self._hasher.hash(plain_password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return self._hasher.verify(plain_password, hashed_password)

    def check_needs_rehash(self, hashed_password: str) -> bool:
        return self._hasher.check_needs_rehash(hashed_password)

    def verify_dummy(self, plain_password: str) -> None:
        try:
            self._hasher.verify(plain_password, self._dummy_hash)
        except Exception:
            pass





def create_access_token(data: dict[str, Any]) -> str:
    to_encode: dict[str, Any] = data.copy()

    # datetime.utcnow()  # deprecated
    expire: datetime = datetime.now(timezone.utc) + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        payload: dict[str, Any] = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    # Check if token is blacklisted
    if await redis_client.exists(f"blacklist:{token}"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    credentials_exception: HTTPException = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload: dict[str, Any] | None = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    user: User | None = await User.get_or_none(id=int(user_id))
    if user is None:
        raise credentials_exception
    return user
