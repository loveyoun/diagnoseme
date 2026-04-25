"""
services/cancer_api.py
-----------------------
국립암센터 공공 API를 호출하는 서비스입니다.

사용하는 API (모두 data.go.kr에서 별도 활용신청 필요):

1. 국가암정보센터 - 내가 알고 싶은 암 (암종별 증상/진단/치료)
   - 공공데이터포털 ID: 15122210
   - 베이스 URL: http://apis.data.go.kr/1262430/CancerInfoService2
   - 참고: https://www.data.go.kr/data/15122210/openapi.do

2. 국가암정보센터 - 암정보사전 (의학 용어 설명)
   - 공공데이터포털 ID: 15122232
   - 베이스 URL: http://apis.data.go.kr/1262430/CancerDicService
   - 참고: https://www.data.go.kr/data/15122232/openapi.do

3. 국가암정보센터 - 통계로 보는 암 (발생률/생존율 통계)
   - 공공데이터포털 ID: 15122208
   - 베이스 URL: http://apis.data.go.kr/1262430/CancerStatService
   - 참고: https://www.data.go.kr/data/15122208/openapi.do

⚠️  주의: 위 엔드포인트는 공공데이터포털의 API 명세를 기반으로 작성되었습니다.
    실제 운영 전에 data.go.kr에서 각 API의 Swagger UI를 통해
    정확한 파라미터명과 응답 구조를 반드시 확인하세요.
    API 키 발급 후 포털의 샘플 코드를 참고하는 것을 권장합니다.
"""

import asyncio
import logging
from typing import Optional

import httpx

from app.core import config

logger = logging.getLogger(__name__)

# 공공 API 공통 타임아웃 (초)
# 공공 API는 응답이 느릴 수 있으므로 넉넉하게 설정합니다
API_TIMEOUT = 10.0


def _build_common_params(extra: dict = None) -> dict:
    """
    모든 공공 API 호출에 공통으로 들어가는 파라미터를 반환합니다.
    serviceKey는 URL 인코딩 없이 전달해야 하는 경우가 있어서
    httpx params 딕셔너리로 전달합니다.
    """
    params = {
        "serviceKey": config.DATA_GO_KR_API_KEY,
        "type": "json",          # XML 대신 JSON 응답 요청
        "numOfRows": 5,          # 최대 5개 결과
        "pageNo": 1,
    }
    if extra:
        params.update(extra)
    return params


async def fetch_cancer_info(cancer_type: str) -> Optional[str]:
    """
    국가암정보센터 API에서 특정 암종의 증상/진단/치료 정보를 가져옵니다.

    Args:
        cancer_type: 암 종류 (예: "폐암", "대장암", "위암")

    Returns:
        암 정보 텍스트 또는 None (실패 시)
    """
    url = f"{config.NCC_CANCER_INFO_BASE_URL}/CancerInfoService2/getCancerInfoList2"
    params = _build_common_params({"cancerTypeName": cancer_type})

    try:
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            # 공공 API 응답 구조: {"response": {"body": {"items": {"item": [...]}}}}
            items = (
                data.get("response", {})
                    .get("body", {})
                    .get("items", {})
                    .get("item", [])
            )

            if not items:
                logger.warning(f"암 정보 없음: cancer_type={cancer_type}")
                return None

            # 여러 항목을 하나의 텍스트로 합침
            # 실제 응답 필드명은 API Swagger에서 확인 후 조정 필요
            result_parts = []
            for item in items[:3]:  # 최대 3개
                info_type = item.get("cancerInfoTypeName", "")
                content = item.get("cancerInfoContent", "") or item.get("content", "")
                if content:
                    result_parts.append(f"[{info_type}]\n{content}")

            return "\n\n".join(result_parts) if result_parts else None

    except httpx.TimeoutException:
        logger.error(f"암 정보 API 타임아웃: cancer_type={cancer_type}")
        return None
    except httpx.HTTPStatusError as e:
        logger.error(f"암 정보 API HTTP 에러: {e.response.status_code}")
        return None
    except Exception as e:
        logger.error(f"암 정보 API 예외: {e}")
        return None


async def fetch_cancer_dictionary(keyword: str) -> Optional[str]:
    """
    암정보사전 API에서 의학 용어 설명을 가져옵니다.
    사용자가 "종양 마커", "전이" 같은 용어를 사용했을 때 활용합니다.

    Args:
        keyword: 검색할 의학 용어

    Returns:
        용어 설명 텍스트 또는 None (실패 시)
    """
    url = f"{config.NCC_CANCER_INFO_BASE_URL}/CancerDicService/getCancerDicList"
    params = _build_common_params({"searchWord": keyword})

    try:
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            items = (
                data.get("response", {})
                    .get("body", {})
                    .get("items", {})
                    .get("item", [])
            )

            if not items:
                return None

            # 사전 용어 설명을 텍스트로 조합
            result_parts = []
            for item in items[:3]:
                term = item.get("word", "") or item.get("term", "")
                definition = item.get("definition", "") or item.get("content", "")
                if term and definition:
                    result_parts.append(f"▪ {term}: {definition}")

            return "\n".join(result_parts) if result_parts else None

    except Exception as e:
        logger.error(f"암정보사전 API 에러: {e}")
        return None


async def fetch_cancer_statistics(cancer_type: str) -> Optional[str]:
    """
    통계로 보는 암 API에서 발생률, 생존율 통계를 가져옵니다.

    Args:
        cancer_type: 암 종류 (예: "폐암")

    Returns:
        통계 정보 텍스트 또는 None (실패 시)
    """
    url = f"{config.NCC_CANCER_INFO_BASE_URL}/CancerStatService/getCancerStatList"
    params = _build_common_params({"cancerTypeName": cancer_type})

    try:
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            items = (
                data.get("response", {})
                    .get("body", {})
                    .get("items", {})
                    .get("item", [])
            )

            if not items:
                return None

            result_parts = []
            for item in items[:3]:
                stat_type = item.get("statTypeName", "")
                stat_value = item.get("statValue", "") or item.get("value", "")
                if stat_type and stat_value:
                    result_parts.append(f"▪ {stat_type}: {stat_value}")

            return "\n".join(result_parts) if result_parts else None

    except Exception as e:
        logger.error(f"암 통계 API 에러: {e}")
        return None


async def fetch_all_cancer_data(
    cancer_type: str,
    keyword: str = None
) -> dict:
    """
    세 개의 API를 asyncio.gather로 동시에 호출합니다.
    순차 호출 대비 응답 시간을 단축합니다.

    예: 각 API가 2초씩 걸린다면
        순차: 2+2+2 = 6초
        동시: max(2,2,2) = 2초

    Args:
        cancer_type: 주 암종 키워드 (예: "폐암")
        keyword: 사전 검색 키워드 (없으면 cancer_type 사용)

    Returns:
        {
            "cancer_info": "암종 기본 정보 텍스트",
            "cancer_stats": "통계 텍스트",
            "cancer_dictionary": "용어 설명 텍스트",
            "sources_used": ["API1", "API2", ...]  # 성공한 API 목록
        }
    """
    search_keyword = keyword or cancer_type

    # 세 API를 동시에 호출 (각각 실패해도 다른 것에 영향 없음)
    cancer_info, cancer_stats, cancer_dict = await asyncio.gather(
        fetch_cancer_info(cancer_type),
        fetch_cancer_statistics(cancer_type),
        fetch_cancer_dictionary(search_keyword),
        return_exceptions=True  # 예외가 발생해도 None으로 처리
    )

    # return_exceptions=True 이면 예외 객체가 반환될 수 있어서 None으로 정규화
    def normalize(result):
        if isinstance(result, Exception):
            logger.error(f"API 호출 예외: {result}")
            return None
        return result

    cancer_info = normalize(cancer_info)
    cancer_stats = normalize(cancer_stats)
    cancer_dict = normalize(cancer_dict)

    # 어떤 API에서 데이터를 가져왔는지 추적
    sources_used = []
    if cancer_info:
        sources_used.append("국가암정보센터_암종정보")
    if cancer_stats:
        sources_used.append("국가암정보센터_통계")
    if cancer_dict:
        sources_used.append("국가암정보센터_사전")

    return {
        "cancer_info": cancer_info,
        "cancer_stats": cancer_stats,
        "cancer_dictionary": cancer_dict,
        "sources_used": sources_used,
    }