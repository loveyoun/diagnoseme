import json

from redis.asyncio import Redis

from app.core.redis import redis_client

PERMISSION_CACHE_TTL = 60


class PermissionCacheService:
    def __init__(self, redis: Redis = redis_client):
        self._redis = redis

    def _key(self, user_id: int) -> str:
        return f"permissions:{user_id}"

    async def get(self, user_id: int) -> set[str] | None:
        """캐시된 권한을 조회합니다. 캐시 미스면 None."""
        try:
            raw = await self._redis.get(self._key(user_id))
            if raw is not None:
                return set(json.loads(raw))
            return None
        except Exception:
            return None

    async def set(self, user_id: int, permissions: set[str]) -> None:
        """권한을 캐시에 저장합니다."""
        try:
            await self._redis.setex(
                self._key(user_id),
                PERMISSION_CACHE_TTL,
                json.dumps(sorted(permissions)),
            )
        except Exception:
            pass

    async def invalidate(self, user_id: int) -> None:
        """특정 사용자의 권한 캐시를 삭제합니다."""
        try:
            await self._redis.delete(self._key(user_id))
        except Exception:
            pass


permission_cache = PermissionCacheService()
