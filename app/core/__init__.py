from fastapi import Request

from app.core.config import Config
from app.core.security import PasswordHasher


def get_config() -> Config:
    return Config()


def password_hasher() -> PasswordHasher:
    return PasswordHasher()


# def get_redis() -> Redis:
#     return Redis(connection_pool=pool)
def get_redis(request: Request):
    return request.app.state.redis


# 모듈 단위로 미리 주입
config: Config = get_config()
password_hasher: PasswordHasher = password_hasher()
# redis_client: Redis = get_redis()
