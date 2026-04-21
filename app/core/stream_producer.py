import json
import uuid

from redis.asyncio import Redis

# ─────────────────────────────────────────────
# Redis Stream 발행
# maxlen으로 스트림 크기 제한 (메모리 관리)
# ─────────────────────────────────────────────

STREAM_KEY = "stream:appointments"
STREAM_MAX_LEN = 100_000  # 최대 메시지 수 (approx(~ 연산자) 사용)


async def stream_enqueue_appointment(
        redis: Redis,
        user_id: int,
        slot_id: int,
        idem_key: str,
        extra: dict | None = None,
) -> str:
    """
    예약 요청을 Redis Stream에 발행.
    Return:
        Stream message ID (polling/SSE의 tracking ID로 활용 가능)
    """
    msg = {
        "user_id": user_id,
        "slot_id": slot_id,
        "idem_key": idem_key,
        "request_id": str(uuid.uuid4()),  # 내부 추적용
        **(extra or {}),
    }
    # XADD MAXLEN ~ 100000: 오래된 메시지 자동 정리 (approx trim, O(1))
    msg_id = await redis.xadd(
        STREAM_KEY,
        {k: json.dumps(v) if isinstance(v, dict) else str(v) for k, v in msg.items()},
        maxlen=STREAM_MAX_LEN,

        # actual stream length may be slightly more than maxlen for performance
        approximate=True,
    )
    return msg_id.decode()
