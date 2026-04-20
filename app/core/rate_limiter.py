import random
import time

from fastapi import HTTPException
from redis.asyncio import Redis

# ─────────────────────────────────────────────
# Token Bucket Rate Limiter (Lua 스크립트)
# Redis에서 원자적으로 실행되므로 race condition 없음
# ─────────────────────────────────────────────

# Lua 스크립트: KEYS[1]=버킷키, ARGV[1]=최대토큰, ARGV[2]=초당리필량, ARGV[3]=현재시각(ms), ARGV[4]=소비토큰수
TOKEN_BUCKET_LUA = """
local key        = KEYS[1]
local capacity   = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])   -- 초당 리필되는 토큰 수
local now        = tonumber(ARGV[3])    -- milliseconds
local requested  = tonumber(ARGV[4])    -- 이번 요청에서 cost할 토큰 (보통 1)

-- 1. 버킷 상태 조회 (tokens: 현재 잔여, last_ms: 마지막 리필 시각)
local data = redis.call('HMGET', key, 'tokens', 'last_ms')
local tokens    = tonumber(data[1])
local last_ms   = tonumber(data[2])

-- 2. 최초요청: 버킷이 없으면 초기화
if tokens == nil then
    tokens  = capacity
    last_ms = now
end

-- 3. 경과 시간만큼 토큰 리필 (최대 capacity까지)
local elapsed_sec = (now - last_ms) / 1000.0
local refilled    = math.min(capacity, tokens + elapsed_sec * refill_rate)

-- TTL: 버킷이 꽉 찰 때까지 걸리는 시간 + 여유 (빈 버킷 자동 정리)
local ttl_sec = math.ceil(capacity / refill_rate) + 10

-- 4-1. 토큰이 충분하면 소비 후 허용, HMSET
if refilled >= requested then
    local remaining = refilled - requested
    redis.call('HSET', key, 'tokens', remaining, 'last_ms', now)
    redis.call('EXPIRE', key, ttl_sec)
    
    -- {허용여부, 잔여토큰}
    return {1, math.floor(remaining)}   
end

-- 4-2. 토큰 부족: 상태만 업데이트하고 거절
redis.call('HSET', key, 'tokens', refilled, 'last_ms', now)
redis.call('EXPIRE', key, ttl_sec)
return {0, 0}
"""


class TokenBucketRateLimiter:
    def __init__(
            self,
            redis: Redis,
            capacity: int = 100,  # 버킷 최대 토큰 수
            refill_rate: float = 10.0,  # 초당 리필 토큰 수
    ):
        self.redis = redis
        self.capacity = capacity
        self.refill_rate = refill_rate

        # Lua 스크립트를 Redis에 등록 (SHA1 캐싱으로 네트워크 절약)
        self._script = self.redis.register_script(TOKEN_BUCKET_LUA)

    async def _check(self, key: str, cost: int = 1) -> tuple[bool, int]:
        """
        Parameter:
            key: 버킷 식별자 (예: "ratelimit:global" 또는 "ratelimit:user:{user_id}")
            cost: 이 요청이 소비할 토큰 수 (기본 1)
        Return:
             (허용여부, 잔여토큰)
        """
        now_ms = int(time.time() * 1000)
        result = await self._script(
            keys=[key],
            args=[self.capacity, self.refill_rate, now_ms, cost],
        )
        allowed = bool(result[0])
        remaining = int(result[1])
        return allowed, remaining

    async def enforce(self, key: str, cost: int = 1):
        allowed, remaining = await self._check(key, cost)
        if not allowed:
            # 1. 이론적인 최소 대기 시간 계산
            base_delay = cost / self.refill_rate

            # 2. 안전 마진(Padding) 추가:
            # 서버와 클라이언트 간의 미세한 오차를 극복하기 위해 10% 정도 더 기다리게 함
            padded_delay = base_delay * 1.1

            # 3. 지터(Jitter) 추가:
            # 모든 클라이언트가 동시에 몰리지 않도록 0~20ms 정도 무작위 시간 추가
            jitter = random.uniform(0, 0.02)

            # 최종 대기 시간 (소수점 2자리 반올림)
            retry_after = round(padded_delay + jitter, 2)
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "rate_limit_exceeded",
                    "retry_after_sec": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )
        return remaining
