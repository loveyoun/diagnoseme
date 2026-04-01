from redis.asyncio import ConnectionPool, Redis

from app.core import config

pool = ConnectionPool.from_url(
    f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}",
    password=config.REDIS_PASSWORD,
    max_connections=10,
    decode_responses=True,
)
redis_client = Redis(connection_pool=pool)


async def get_redis() -> Redis:
    return redis_client
