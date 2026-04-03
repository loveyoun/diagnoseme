from redis.asyncio import ConnectionPool, Redis

from app.core import config

pool: ConnectionPool = ConnectionPool.from_url(
    f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}",
    password=str(config.REDIS_PASSWORD) if config.REDIS_PASSWORD is not None else None,
    max_connections=10,
    decode_responses=True,
)
redis_client: Redis = Redis(connection_pool=pool)


async def get_redis() -> Redis:
    return redis_client
