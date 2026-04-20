import asyncio
import json
import logging

from redis.asyncio import Redis

from app.core.admission_control import AdmissionControl
from app.core.stream_producer import STREAM_KEY

logger = logging.getLogger(__name__)

GROUP_NAME = "appointment_workers"
CONSUMER_NAME = "worker-1"  # 인스턴스마다 고유하게 (hostname 등 활용)

# ─────────────────────────────────────────────
# Worker 장애 복구 파라미터
# CLAIM_IDLE_MS: 이 시간 이상 ACK 없으면 stale로 간주
# MAX_RETRY: 재처리 최대 횟수 (초과 시 DLQ로)
# ─────────────────────────────────────────────
CLAIM_IDLE_MS = 30_000  # 30초 이상 pending이면 stale
MAX_RETRY = 3
DLQ_STREAM = "appointments:dlq"


class ReservationWorker:
    def __init__(self, redis: Redis, admission: AdmissionControl):
        self.redis = redis
        self.admission = admission

    async def setup(self):
        """Consumer Group 생성 (이미 있으면 무시)"""
        try:
            await self.redis.xgroup_create(
                STREAM_KEY, GROUP_NAME, id="0", mkstream=True
            )
        except Exception as e:
            if "BUSYGROUP" not in str(e):
                raise

    async def process_message(self, msg_id: str, data: dict):
        """실제 예약 처리 로직"""
        user_id = data["user_id"]
        slot_id = data["slot_id"]
        idem_key = data["idem_key"]

        try:
            # ── DB 저장 (tortoise ORM) ──
            # await Reservation.create(user_id=user_id, slot_id=slot_id, ...)

            # ── 완료 마킹 ──
            result = {"reservation_id": "...", "slot_id": slot_id}
            await self.admission.mark_complete(user_id, idem_key, result)

            # ── SSE/polling 결과 Redis에 저장 ──
            await self.redis.setex(
                f"result:{idem_key}", 3600, json.dumps(result)
            )

            logger.info(f"[OK] msg={msg_id} user={user_id} slot={slot_id}")

        except Exception as e:
            logger.error(f"[FAIL] msg={msg_id} error={e}")
            raise  # ACK 안 함 → PEL에 잔류

    async def run(self):
        """메인 consume 루프"""
        await self.setup()
        logger.info(f"Worker {CONSUMER_NAME} started")

        while True:
            try:
                # XREADGROUP: 내 consumer에 할당된 새 메시지 읽기
                # count=10: 한 번에 최대 10개, block=5000: 5초 대기
                messages = await self.redis.xreadgroup(
                    GROUP_NAME,
                    CONSUMER_NAME,
                    {STREAM_KEY: ">"},  # ">"는 신규 메시지만
                    count=10,
                    block=5000,
                )

                if messages:
                    for stream, msgs in messages:
                        for msg_id, raw in msgs:
                            data = {
                                k.decode(): v.decode() for k, v in raw.items()
                            }
                            try:
                                await self.process_message(msg_id.decode(), data)
                                # 성공 시에만 ACK
                                await self.redis.xack(STREAM_KEY, GROUP_NAME, msg_id)
                            except Exception:
                                pass  # PEL 잔류, recovery worker가 처리

                # 주기적으로 stale 메시지 복구 시도
                await self._recover_stale()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Consumer loop error: {e}")
                await asyncio.sleep(1)

    async def _recover_stale(self):
        """
        XAUTOCLAIM: CLAIM_IDLE_MS 이상 pending인 메시지를 내 consumer로 가져옴.
        Worker 크래시, 네트워크 단절 등으로 ACK 못한 메시지 복구.
        """
        try:
            # XAUTOCLAIM은 Redis 6.2+
            # 반환: (next_start_id, [(msg_id, data), ...], deleted_ids)
            result = await self.redis.xautoclaim(
                STREAM_KEY,
                GROUP_NAME,
                CONSUMER_NAME,
                min_idle_time=CLAIM_IDLE_MS,
                start_id="0-0",
                count=5,
            )
            _, claimed_msgs, _ = result

            for msg_id, raw in claimed_msgs:
                data = {k.decode(): v.decode() for k, v in raw.items()}
                retry_count = int(data.get("_retry", "0"))

                if retry_count >= MAX_RETRY:
                    # ── Dead Letter Queue로 이동 ──
                    logger.warning(f"[DLQ] msg={msg_id} exceeded max retry")
                    await self.redis.xadd(DLQ_STREAM, {**raw, b"_failed_id": msg_id})
                    await self.redis.xack(STREAM_KEY, GROUP_NAME, msg_id)

                    # 슬롯 예약 롤백 (정원에서 제거)
                    await self.admission.release_slot(
                        data["slot_id"], data["user_id"]
                    )
                    await self.admission.mark_complete(
                        data["user_id"],
                        data["idempotency_key"],
                        {"error": "processing_failed"},
                        success=False,
                    )
                    continue

                # retry_count 증가 후 재처리
                data["_retry"] = str(retry_count + 1)
                try:
                    await self.process_message(msg_id.decode(), data)
                    await self.redis.xack(STREAM_KEY, GROUP_NAME, msg_id)
                except Exception:
                    logger.warning(f"[RETRY {retry_count + 1}] msg={msg_id}")

        except Exception as e:
            logger.debug(f"Recovery check error (non-critical): {e}")
