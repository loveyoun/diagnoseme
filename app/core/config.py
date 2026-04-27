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

    # Gemini API 키
    AI_MODEL: str
    AI_API_KEY: str

    # -------------------------
    # 공공데이터포털 API 키
    # 국립암센터 API(B551172)와 국가암정보센터 API(15122210 등)는
    # 같은 포털에서 발급되지만 서비스별로 별도 신청이 필요합니다.
    # -------------------------
    DATA_GO_KR_API_KEY: str = "YOUR_DATA_GO_KR_API_KEY"
    NCC_API_BASE_URL: str = "http://apis.data.go.kr/B551172"
    NCC_CANCER_INFO_BASE_URL: str = "http://apis.data.go.kr/1262430"  # 국가암정보센터

    # -------------------------
    # ChromaDB (벡터 DB) 설정
    # 로컬 디스크에 벡터 데이터를 영구 저장하는 경로
    # -------------------------
    CHROMA_PERSIST_DIR: str = "./chroma_db"
