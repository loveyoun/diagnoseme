from enum import StrEnum

from pydantic_settings import BaseSettings, SettingsConfigDict


class Env(StrEnum):
    LOCAL = "local"
    STAGE = "stage"
    PROD = "prod"


# __init__.py에서 싱글톤 유지
# sys.modules에 캐싱
class Config(BaseSettings):
    # extra: 일단 그외 정보 받아주기
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")

    ENV: Env = Env.LOCAL

    DEBUG: bool = False

    DB_HOST: str
    DB_PORT: int = 5432
    POSTGRES_USER: str = "admin"
    POSTGRES_PASSWORD: str = "1234"
    POSTGRES_DB: str = "dm"
    CONNECT_TIMEOUT: int = 5
    CONNECTION_POOL_MAXSIZE: int = 10
    TZ: str = "Asia/Seoul"

    NAVER_CLIENT_ID: str
    NAVER_CLIENT_SECRET: str
    NAVER_REDIRECT_URI: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    REDIS_HOST: str
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | int | None = None
