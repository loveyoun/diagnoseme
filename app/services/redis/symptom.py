"""
services/redis_service.py
--------------------------
Redis를 이용한 캐싱 서비스입니다.

캐싱 전략:
- 키: 사용자 증상 텍스트를 SHA-256 해싱한 값
- 값: AI 최종 응답 JSON 문자열
- TTL: config에서 설정한 시간(기본 1시간)

이점:
- 동일한 증상이 반복 입력될 때 공공 API + AI 호출을 스킵해서 응답 속도를 높입니다.
- 공공 API의 일일 호출 한도(10,000건)를 아낄 수 있습니다.
"""
from app.core import get_redis
import hashlib
import json
import logging

import redis.asyncio as aioredis

from app.core import config

logger = logging.getLogger(__name__)


def _make_cache_key(symptom: str) -> str:
    """
    증상 텍스트를 SHA-256 해시로 변환해서 Redis 키로 씁니다.
    같은 문자열은 항상 같은 키가 나옵니다.
    공백 정규화(strip)를 해서 앞뒤 공백 차이로 캐시 미스가 나는 걸 방지합니다.
    """
    normalized = symptom.strip().lower()
    return f"symptom:v1:{hashlib.sha256(normalized.encode()).hexdigest()}"


async def get_redis_client() -> aioredis.Redis:
    """
    Redis 클라이언트를 생성해서 반환합니다.
    연결 실패 시 None을 반환해서 캐시 없이 진행할 수 있도록 합니다.
    (Redis가 없어도 서비스가 죽지 않도록 방어 처리)
    """
    try:
        client = aioredis.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            decode_responses=True,  # bytes 대신 str로 반환
        )
        # 연결 확인
        await client.ping()
        return client
    except Exception as e:
        logger.warning(f"Redis 연결 실패 (캐시 없이 진행): {e}")
        return None


async def get_cached_response(symptom: str) -> dict | None:
    """
    Redis에서 캐시된 응답을 조회합니다.

    Returns:
        dict: 캐시 히트 시 저장된 응답 딕셔너리
        None: 캐시 미스 또는 Redis 연결 실패
    """
    client = await get_redis_client()
    if client is None:
        return None

    try:
        key = _make_cache_key(symptom)
        cached = await client.get(key)

        if cached:
            logger.info(f"Redis 캐시 히트: key={key[:16]}...")
            return json.loads(cached)

        logger.info(f"Redis 캐시 미스: key={key[:16]}...")
        return None

    except Exception as e:
        logger.error(f"Redis 조회 중 에러: {e}")
        return None
    finally:
        await client.aclose()


async def set_cached_response(symptom: str, response_data: dict) -> None:
    """
    AI 분석 결과를 Redis에 저장합니다.

    Args:
        symptom: 원본 증상 텍스트 (키 생성용)
        response_data: 저장할 응답 딕셔너리
    """
    client = await get_redis_client()
    if client is None:
        return  # Redis 없으면 저장 스킵 (에러로 처리 안 함)

    try:
        key = _make_cache_key(symptom)
        # json.dumps로 직렬화 후 저장, TTL 설정
        await client.setex(
            name=key,
            time=3600,
            value=json.dumps(response_data, ensure_ascii=False)
        )
        logger.info(f"Redis 캐시 저장: key={key[:16]}... TTL={3600}초")

    except Exception as e:
        logger.error(f"Redis 저장 중 에러: {e}")
    finally:
        await client.aclose()
