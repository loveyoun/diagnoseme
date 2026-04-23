from typing import Any

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
                "connect_timeout": config.CONNECT_TIMEOUT,
                "maxsize": config.CONNECTION_POOL_MAXSIZE,
            },
        },
    },
    "apps": {
        "models": {
            "models": TORTOISE_APP_MODELS,
            "default_connection": "default",
        },
    },
    "timezone": config.TZ,
}

# from tortoise import Tortoise
# from fastapi import FastAPI
# from tortoise.contrib.fastapi import register_tortoise
#
#
# def initialize_tortoise(app: FastAPI) -> None:
#     # import 타이밍 이슈: 모델 메타데이터를 선등록
#     Tortoise.init_models(TORTOISE_APP_MODELS, "models")
#
#     # connection 초기화, app lifespan과 DB lifecycle 연결
#     # 내부적으로 @app.on_event() 씀.
#     register_tortoise(app, config=TORTOISE_ORM, generate_schemas=False)
#
#     # -----------------------
#     @app.on_event("startup")  # deprecated
#     async def verify_db():
#         print("🔍 DB 연결 확인 시도 중...")
#         conn = Tortoise.get_connection("default")
#         result = await conn.execute_query_dict("SELECT 1")
#         print(f"✅ DB 연결 성공! 결과: {result}")
#     # -----------------------
