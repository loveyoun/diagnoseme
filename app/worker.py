# Worker 진입점
import asyncio
import os
import socket

from redis.asyncio import Redis

from app.core import get_redis
from app.core.admission_control import AdmissionControl
from app.worker.consumer import AppointmentWorker

# 인스턴스마다 고유하게 (hostname 등 활용)
unique_worker = f"{socket.gethostname()}:{os.getpid()}"
CONSUMER_NAME_1 = "worker-1"
CONSUMER_NAME_2 = "worker-2"


async def main():
    redis: Redis = get_redis()
    admission = AdmissionControl(redis)
    worker = AppointmentWorker(redis, admission, consumer_name=unique_worker)
    # worker1 = AppointmentWorker(redis, admission, CONSUMER_NAME_1)
    # worker2 = AppointmentWorker(redis, admission, CONSUMER_NAME_2)
    await worker.run()
    # await asyncio.gather(
    #     worker1.run(),
    #     worker2.run(),
    # )


if __name__ == "__main__":
    asyncio.run(main())
