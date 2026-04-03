from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from redis.asyncio import Redis

from app.core import config
from app.models.user import User

oauth2_scheme: OAuth2PasswordBearer = OAuth2PasswordBearer(tokenUrl="/auth/signin")

pwd_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")
redis_client: Redis = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


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
