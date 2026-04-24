import pytest_asyncio
from tortoise.contrib.test import tortoise_test_context

from app.core import config
from app.db.database import TORTOISE_APP_MODELS

DATABASE_URL = f"postgresql+psycopg://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/test"
TEST_DB_LABEL = "models"
TEST_DB_TZ = "Asia/Seoul"


@pytest_asyncio.fixture(autouse=True, scope="session")
async def db():
    async with tortoise_test_context(
            modules=TORTOISE_APP_MODELS,
            db_url=DATABASE_URL,
            app_label=TEST_DB_LABEL,
            connection_label="default",
    ) as ctx:
        yield ctx
