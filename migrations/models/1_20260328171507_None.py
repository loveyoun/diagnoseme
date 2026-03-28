from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "users" (
    "user_id" BIGSERIAL NOT NULL PRIMARY KEY,
    "nickname" VARCHAR(100),
    "email" VARCHAR(255),
    "gender" VARCHAR(1),
    "naver_id" VARCHAR(100) NOT NULL UNIQUE,
    "name" VARCHAR(100),
    "birthday" VARCHAR(5),
    "birthyear" VARCHAR(4),
    "profile_image" VARCHAR(500)
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
