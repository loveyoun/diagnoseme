from app.core.config import Config
from app.core.security import PasswordHasher


def get_config() -> Config:
    return Config()


def password_hasher() -> PasswordHasher:
    return PasswordHasher()


# 모듈 단위로 미리 주입
config: Config = get_config()
password_hasher: PasswordHasher = password_hasher()
