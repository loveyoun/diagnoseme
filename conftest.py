import asyncio
from typing import Any, Generator
from unittest.mock import Mock, patch

import pytest
import pytest_asyncio
from pytest import FixtureRequest
from tortoise.backends.base.config_generator import generate_config

from app.core import config
from app.db.database import TORTOISE_APP_MODELS

# TEST_BASE_URL = "http://test"
TEST_DB_LABEL = "models"
TEST_DB_TZ = "Asia/Seoul"


def get_test_db_config() -> dict[str, Any]:
    tortoise_config = generate_config(
        db_url=f"mysql://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/test",
        testing=True,
        app_modules={TEST_DB_LABEL: TORTOISE_APP_MODELS},
        connection_label=TEST_DB_LABEL,
    )
    tortoise_config["timezone"] = TEST_DB_TZ

    return tortoise_config


@pytest.fixture(scope="session", autouse=True)
def initialize(request: FixtureRequest) -> Generator[None, None]:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # DB 연결 및 스키마 생성 (initializer 역할)
    db_config = get_test_db_config()

    # with patch("tortoise.contrib.test.getDBConfig", Mock(return_value=get_test_db_config())):
    #     request.initializer(modules=TORTOISE_APP_MODELS)
    # yield
    # finalizer()
    # loop.close()


@pytest_asyncio.fixture(autouse=True, scope="session")
def event_loop() -> None:
    pass
