import json
from dataclasses import dataclass
from enum import IntEnum

from fastapi import HTTPException
from redis.asyncio import Redis

# ─────────────────────────────────────────────
# Slot 예약
# 역할 1) Idempotency: 동일 요청(idemp_key) 재시도 시 캐시된 결과 반환
# 역할 2) 중복차단: 같은 user_id가 같은 slot_id에 이중 예약 방지
# 역할 3) 정원 관리: 슬롯당 N명 제한 (SET 기반)
# ─────────────────────────────────────────────

# Lua: 정원 체크 + 예약자 추가를 원자적으로 수행
# SADD가 0이면 이미 예약됨, SCARD가 capacity 초과면 정원 초과
RESERVE_SLOT_LUA = """
-- slot:{slot_id}:members
local key = KEYS[1]   
local capacity    = tonumber(ARGV[1])
local user_id     = ARGV[2]
local ttl         = tonumber(ARGV[3])  -- 슬롯 만료까지 남은 초

-- 1. 이미 예약된 유저인지 확인 (중복 예약 차단)
local already = redis.call('SISMEMBER', key, user_id)
if already == 1 then
    return -1  -- 이미 예약
end

-- 2. 현재 예약자 수 확인 (정원 체크)
-- @remains로 바꾸는 거 고려
local current = redis.call('SCARD', key)
if current >= capacity then
    return 0   -- 정원 초과
end

-- 3. 예약 추가
local key_exists = redis.call('EXISTS', key)
local added = redis.call('SADD', key, user_id)
if key_exists == 0 then
    redis.call('EXPIRE', key, ttl)
end
return 1  -- 예약 성공
"""

'''
Edge Case
1. DB(Application) 레벨에서 최종 정원 체크 로직
2. Redis processing -> Stream/Worker -> DB -> Redis success
3. key EX 시간 고정
redis.call('SADD', key, user_id)
if redis.call('SCARD', key) == 1 then
    redis.call('EXPIRE', key, ttl)
end
'''


class SlotResult(IntEnum):
    ALREADY_RESERVED = -1
    FULL = 0
    OK = 1


@dataclass
class IdempotencyEntry:
    status: str  # "processing" | "success" | "failed"
    result: dict | None  # 완료 시 응답 payload


class AdmissionControl:
    IDEM_SUCCESS_TTL = 86400  # idempotency key 보존 기간 (24h)
    IDEM_PROCESSING_TTL = 30  # 처리 중 임시 TTL (worker 타임아웃보다 길게)

    def __init__(self, redis: Redis):
        self.redis = redis
        self._reserve_script = redis.register_script(RESERVE_SLOT_LUA)

    # ── Idempotency ──────────────────────────────────────────

    def _idem_key(self, user_id: int, idem_key: str) -> str:
        # user_id + 클라이언트 제공키 로 네임스페이스 분리
        # 다른 유저가 같은 idem key를 우연히 쓰는 경우 방지
        return f"idem:{user_id}:{idem_key}"

    async def check_idempotency(
            self, user_id: int, idempotency_key: str
    ) -> IdempotencyEntry | None:
        """
        이미 처리된 요청이면 캐시된 결과 반환.
        처리 중이면 'processing' 상태 반환 (클라이언트가 polling하도록 유도).
        없으면 None 반환 → 신규 요청으로 처리.
        """
        raw = await self.redis.get(self._idem_key(user_id, idempotency_key))
        if raw is None:
            return None
        data = json.loads(raw)  # json -> dict
        return IdempotencyEntry(status=data["status"], result=data.get("result"))

    async def mark_processing(self, user_id: int, idempotency_key: str):
        """요청을 처리 중 상태로 마킹 (짧은 TTL로 시작)"""
        key = self._idem_key(user_id, idempotency_key)
        payload = json.dumps({"status": "processing", "result": None})

        # NX: 이미 있으면 덮어쓰지 않음 (동시 요청 중 하나만 통과)
        set_ok = await self.redis.set(key, payload, ex=self.IDEM_PROCESSING_TTL, nx=True)
        if not set_ok:
            raise HTTPException(409, detail={"error": "duplicate_in_flight"})

    async def mark_complete(
            self, user_id: int, idem_key: str, result: dict, success: bool = True
    ):
        """Worker가 완료 후 호출 → TTL을 24h로 늘리고 결과 저장"""
        key = self._idem_key(user_id, idem_key)
        payload = json.dumps({
            "status": "success" if success else "failed",
            "result": result,
        })
        await self.redis.set(key, payload, ex=self.IDEM_SUCCESS_TTL)

    # ── Slot 정원 관리 ────────────────────────────────────────

    async def try_reserve_slot(
            self,
            slot_id: int,
            user_id: int,
            capacity: int,
            slot_ttl_sec: int,  # 슬롯 이벤트 만료까지 남은 초
    ) -> SlotResult:
        """
        원자적으로 슬롯 예약 시도.
        SlotResult.OK        → 예약 성공, Stream에 발행하면 됨
        SlotResult.FULL      → 정원 초과
        SlotResult.ALREADY_RESERVED → 이미 예약됨 (멱등 처리 가능)
        """
        result = await self._reserve_script(
            keys=[f"slot:{slot_id}:members"],
            args=[capacity, user_id, slot_ttl_sec],
        )
        return SlotResult(result)

    async def release_slot(self, slot_id: int, user_id: int):
        """
        보상 트랜잭션
        Worker 최종실패 후 예약자 제거
        """
        await self.redis.srem(f"slot:{slot_id}:members", user_id)
