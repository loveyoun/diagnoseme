import asyncio
import json
import logging

from redis.asyncio import Redis

from app.core.admission_control import AdmissionControl
from app.core.stream_producer import STREAM_KEY
from app.models import Appointment

logger = logging.getLogger(__name__)

GROUP_NAME = "appointment_workers"
CLAIM_IDLE_MS = 30_000  # 30초 이상 pending이면 stale
MAX_RETRY = 3  # 초과 시 DLQ로
DLQ_STREAM = "appointments:dlq"


class AppointmentWorker:
    def __init__(self, redis: Redis, admission: AdmissionControl, consumer_name:str):
        self.redis = redis
        self.admission = admission
        self.consumer_name=consumer_name

    async def setup(self):
        """ Consumer Group 생성 """
        try:
            await self.redis.xgroup_create(
                STREAM_KEY, GROUP_NAME, id="0", mkstream=True
            )
        except Exception as e:
            if "BUSYGROUP" not in str(e):
                raise

    async def process_message(self, msg_id: str, data: dict):
        """실제 예약 처리 로직"""
        user_id = int(data["user_id"])
        slot_id = int(data["slot_id"])
        idem_key = data["idem_key"]

        try:
            ''' Integrity Handling '''
            # 1. DB 저장
            # Redis session, DB session 연결
            appt = await Appointment.create_appointment(idem_key=idem_key,
                                                        user_id=user_id,
                                                        slot_id=slot_id,
                                                        memo=data.get("memo"))
            # 2. 완료 마킹
            result = {"appointment_id": appt.id, "slot_id": slot_id}
            await self.admission.mark_complete(user_id, idem_key, result)
            await self.redis.setex(f"result:{idem_key}", 3600, json.dumps(result))

            # 3. 성공 시 로그
            logger.info(f"[OK] msg={msg_id} user={user_id} slot={slot_id}")

        except (ValueError, RuntimeError) as e:
            # [중요] 비즈니스 실패: 슬롯 없음/비활성 등은 다시 시도해도 결과가 같음
            # 따라서 결과를 '실패'로 저장하고 ACK를 보내 PEL에서 제거해야 함
            # '실패용 스트림'으로 옮기는 처리를 합니다.
            logger.warning(f"[REJECT] msg={msg_id} logic_error={e}")
            await self.redis.setex(f"result:{data['idem_key']}", 3600, json.dumps({"error": str(e)}))
            await self.redis.xack(STREAM_KEY, GROUP_NAME, msg_id)
            # ← admission.mark_complete(user_id, idem_key, {"error": ...}, success=False)
        except asyncio.CancelledError:
            logger.info("작업 중단 요청을 받았습니다.")
            raise  # 상위 루프(run)로 알림
        except Exception as e:
            # 시스템 실패: DB 다운, 네트워크 에러 등 (다시 시도하면 성공할 수도 있음)
            # ACK를 하지 않고 raise하여 상위 루프에서 PEL에 남기도록 유도
            logger.error(f"[SYSTEM ERROR] msg={msg_id} error={e}")
            raise  # ACK 안 함 → 해당 소비자의 PEL에 잔류

    async def run(self):
        """메인 consume 루프"""
        await self.setup()
        logger.info(f"Worker {self.consumer_name} started")

        while True:
            try:
                # XREADGROUP: 내 consumer에 할당된 새 메시지 읽기
                # count=10: 한 번에 최대 10개, block=5000: 5초 대기
                messages = await self.redis.xreadgroup(
                    GROUP_NAME,
                    self.consumer_name,
                    {STREAM_KEY: ">"},  # ">"는 신규 메시지만
                    count=10,
                    block=5000,
                )

                if messages:
                    for _, msgs in messages:  # stream
                        for msg_id, raw in msgs:
                            data = {k.decode(): v.decode() for k, v in raw.items()}
                            try:
                                """ slot remains 차감 """
                                # 실제 예약 로직 수행
                                await self.process_message(msg_id.decode(), data)
                                # 성공 시에만 ACK
                                await self.redis.xack(STREAM_KEY, GROUP_NAME, msg_id)
                            except Exception:
                                # process_message에서 raise된 시스템 에러가 여기로 옴
                                # ACK를 호출하지 않으므로 자동으로 PEL에 잔류
                                continue  # PEL 잔류, recovery worker가 처리

                # 주기적으로 stale 메시지 복구 시도
                await self._recover_stale()

            # 시스템이 종료되거나 작업이 취소될 때 발생하는 정상 중단 신호
            except asyncio.CancelledError:
                logger.info("Worker shutting down...")
                break
            except Exception as e:
                # 루프 자체의 에러 (Redis 연결 끊김 등)
                logger.error(f"Consumer loop error: {e}")
                await asyncio.sleep(1)  # 잠시 쉬었다가 재시도

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
                self.consumer_name,
                min_idle_time=CLAIM_IDLE_MS,
                start_id="0-0",
                count=5,
            )
            _, claimed_msgs, _ = result

            for msg_id, raw in claimed_msgs:
                data = {k.decode(): v.decode() for k, v in raw.items()}
                retry_count = int(data.get("_retry", "0"))

                if retry_count >= MAX_RETRY:
                    # Dead Letter Queue로 이동
                    logger.warning(f"[DLQ] msg={msg_id} exceeded max retry")
                    await self.redis.xadd(DLQ_STREAM, {**raw, b"_failed_id": msg_id})
                    await self.redis.xack(STREAM_KEY, GROUP_NAME, msg_id)

                    # 슬롯 예약 롤백 (정원에서 제거)
                    await self.admission.release_slot(data["slot_id"], data["user_id"])
                    await self.admission.mark_complete(
                        data["user_id"],
                        data["idem_key"],
                        {"error": "processing_failed"},
                        success=False,
                    )
                    continue

                # retry_count 증가 후 재처리
                data["_retry"] = str(retry_count + 1)  # 로컬 dict만 수정
                # ← Redis stream에 업데이트하는 코드 없음
                # 해결: xdel + xadd로 메시지 교체하거나 별도 카운터 키 사용

                try:
                    # XREADGROUP: bytes.decode()
                    # XAUTOCLAIM: str
                    await self.process_message(msg_id.decode(), data)
                    await self.redis.xack(STREAM_KEY, GROUP_NAME, msg_id)
                except Exception:
                    logger.warning(f"[RETRY {retry_count + 1}] msg={msg_id}")

        except Exception as e:
            logger.debug(f"Recovery check error (non-critical): {e}")
