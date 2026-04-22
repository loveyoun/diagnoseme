# from redis.asyncio import ConnectionPool
#
# from app.core import config
#
# pool: ConnectionPool = ConnectionPool.from_url(  # Redis.from_url()
#     f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}",
#     password=str(config.REDIS_PASSWORD) if config.REDIS_PASSWORD is not None else None,
#     max_connections=10,
#     decode_responses=True,
# )
