from typing import Any

from fastapi import FastAPI
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise

from app.core import config

# Tortoise가 스캔할 모델 모듈 목록
# aerich.models는 마이그레이션 이력 테이블 관리를 위해 반드시 포함
TORTOISE_APP_MODELS: list[str] = [
    "aerich.models",
    "app.models",
]

# ORM 설정
TORTOISE_ORM: dict[str, Any] = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "host": config.DB_HOST,
                "port": config.DB_PORT,
                "user": config.POSTGRES_USER,
                "password": config.POSTGRES_PASSWORD,
                "database": config.POSTGRES_DB,
            },
        },
    },
    "apps": {
        "models": {
            "models": TORTOISE_APP_MODELS,
            "default_connection": "default",
        },
    },
    "timezone": "Asia/Seoul",
}


def initialize_tortoise(app: FastAPI) -> None:
    # import 타이밍 이슈: 모델 메타데이터를 선등록
    Tortoise.init_models(TORTOISE_APP_MODELS, "models")
    # app lifespan과 DB lifecycle 연결
    register_tortoise(app, config=TORTOISE_ORM, generate_schemas=False)
