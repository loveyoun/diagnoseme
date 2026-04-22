"""
 Worker 진입점
"""

import asyncio
import os
import socket

from redis.asyncio import ConnectionPool
from redis.asyncio import Redis

from app.core import config
from app.core.admission_control import AdmissionControl
from app.worker.consumer import AppointmentWorker

# 인스턴스마다 고유하게 (hostname 등 활용)
unique_worker = f"{socket.gethostname()}:{os.getpid()}"
CONSUMER_NAME_1 = "worker-1"
CONSUMER_NAME_2 = "worker-2"


async def main():
    pool: ConnectionPool = ConnectionPool.from_url(  # Redis.from_url()
        f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}",
        password=str(config.REDIS_PASSWORD) if config.REDIS_PASSWORD is not None else None,
        max_connections=10,
        decode_responses=True,
    )
    redis = Redis(connection_pool=pool)
    admission = AdmissionControl(redis)

    # worker1 = AppointmentWorker(redis, admission, CONSUMER_NAME_1)
    # worker2 = AppointmentWorker(redis, admission, CONSUMER_NAME_2)
    # await asyncio.gather(
    #     worker1.run(),
    #     worker2.run(),
    # )

    worker = AppointmentWorker(redis, admission, consumer_name=unique_worker)
    await worker.run()  # Blocking async

    # Non-blocking async
    task = asyncio.create_task(worker.run())
    # 10초 뒤에 강제로 중단시켜보기 테스트
    # await asyncio.sleep(10)
    # task.cancel()
    await task


if __name__ == "__main__":
    asyncio.run(main())
