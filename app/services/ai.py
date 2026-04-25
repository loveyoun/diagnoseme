"""
services/ai_service.py
-----------------------
Google Gemini 2.5 Flash를 사용해서 공공 API 데이터와 증상을 분석하는 서비스입니다.

동작 방식:
1. 공공 API 데이터 + 벡터 검색 결과를 컨텍스트로 조합
2. 시스템 프롬프트로 AI 역할과 제약사항을 지정
3. 사용자 증상과 컨텍스트를 함께 전달해서 분석 요청
4. AI 응답 텍스트를 반환
"""

import logging
from typing import Optional

from google import genai

from app.core import config

logger = logging.getLogger(__name__)

# Gemini 모델 설정
# gemini-2.5-flash: 빠르고 비용 효율적인 모델
GEMINI_MODEL = "gemini-2.5-flash"

# AI 응답 생성 설정
GENERATION_CONFIG = genai.types.GenerationConfig(
    temperature=0.3,       # 낮을수록 일관된 응답 (의료 정보이므로 낮게 설정)
    max_output_tokens=1500,  # 최대 응답 길이
    top_p=0.8,
)

# 시스템 프롬프트: AI의 역할과 절대 지켜야 할 규칙을 정의합니다
SYSTEM_PROMPT = """당신은 국립암센터 공공데이터를 기반으로 암 관련 건강 정보를 안내하는 도우미입니다.

[반드시 지켜야 할 규칙]
1. "암입니다", "암이 의심됩니다", "암일 가능성이 높습니다" 같은 단정적 진단 표현은 절대 사용하지 마세요.
2. 제공된 [공공데이터] 내용을 우선적으로 활용하고, 없는 내용은 추측하지 마세요.
3. 반드시 "정확한 진단은 전문의에게 받으세요"라는 문구를 포함하세요.
4. 관련 진료과(예: 호흡기내과, 종양내과 등)를 안내하세요.
5. 응답은 반드시 한국어로 작성하세요.
6. 응답 형식:
   - 📋 증상 분석 요약 (2~3문장)
   - 🔍 관련 가능 암종 (데이터 기반, 단정하지 말고 "관련 가능성이 있는 암종" 표현 사용)
   - 🏥 권장 진료과
   - ⚠️ 주의사항 및 조기검진 안내
"""


def _build_user_prompt(
    symptom: str,
    age: Optional[int],
    gender: Optional[str],
    cancer_info: Optional[str],
    cancer_stats: Optional[str],
    cancer_dictionary: Optional[str],
    similar_cases: Optional[str],
) -> str:
    """
    AI에게 전달할 사용자 프롬프트를 구성합니다.
    공공 API 데이터를 컨텍스트로 포함시켜서 AI가 근거 있는 답변을 하도록 유도합니다.
    데이터가 없는 섹션은 "데이터 없음"으로 표시합니다.
    """
    # 사용자 기본 정보 섹션
    user_info_parts = [f"증상: {symptom}"]
    if age:
        user_info_parts.append(f"나이: {age}세")
    if gender:
        user_info_parts.append(f"성별: {gender}")
    user_info = " | ".join(user_info_parts)

    # 공공 API 데이터 섹션 (있는 것만 포함)
    context_sections = []

    if cancer_info:
        context_sections.append(f"[암종 정보 - 국가암정보센터]\n{cancer_info}")
    else:
        context_sections.append("[암종 정보] 조회 데이터 없음")

    if cancer_stats:
        context_sections.append(f"[발생률/생존율 통계 - 국가암정보센터]\n{cancer_stats}")

    if cancer_dictionary:
        context_sections.append(f"[관련 의학 용어 설명]\n{cancer_dictionary}")

    if similar_cases:
        context_sections.append(f"[유사 증상 관련 문서 - 벡터 검색]\n{similar_cases}")

    context_text = "\n\n".join(context_sections)

    return f"""[사용자 정보]
{user_info}

[공공데이터 컨텍스트]
{context_text}

위 공공데이터를 참고하여 사용자의 증상에 대해 정해진 형식으로 안내해 주세요."""


async def analyze_symptom_with_ai(
    symptom: str,
    age: Optional[int] = None,
    gender: Optional[str] = None,
    cancer_info: Optional[str] = None,
    cancer_stats: Optional[str] = None,
    cancer_dictionary: Optional[str] = None,
    similar_cases: Optional[str] = None,
) -> str:
    """
    Gemini AI를 호출해서 증상을 분석하고 응답을 반환합니다.

    Args:
        symptom: 사용자 증상 텍스트
        age: 나이 (선택)
        gender: 성별 (선택)
        cancer_info: 공공 API에서 가져온 암종 정보
        cancer_stats: 공공 API에서 가져온 통계 정보
        cancer_dictionary: 공공 API에서 가져온 용어 설명
        similar_cases: 벡터 DB에서 검색된 유사 사례

    Returns:
        AI가 생성한 분석 결과 텍스트
    """
    try:
        # Gemini 클라이언트 초기화
        genai.configure(api_key=config.AI_API_KEY)
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=SYSTEM_PROMPT,
            generation_config=GENERATION_CONFIG,
        )

        # 프롬프트 구성
        user_prompt = _build_user_prompt(
            symptom=symptom,
            age=age,
            gender=gender,
            cancer_info=cancer_info,
            cancer_stats=cancer_stats,
            cancer_dictionary=cancer_dictionary,
            similar_cases=similar_cases,
        )

        logger.info(f"Gemini API 호출 시작: model={GEMINI_MODEL}")

        # Gemini API 비동기 호출
        # generate_content_async: 비동기 버전
        response = await model.generate_content_async(user_prompt)

        if not response.text:
            logger.warning("Gemini API 응답이 비어있음")
            return "AI 분석 결과를 생성하지 못했습니다. 잠시 후 다시 시도해 주세요."

        logger.info("Gemini API 호출 완료")
        return response.text

    except Exception as e:
        logger.error(f"Gemini API 호출 실패: {e}")
        # AI 호출 실패 시 공공 데이터 기반 폴백 메시지 반환
        return _fallback_response(symptom, cancer_info)


def _fallback_response(symptom: str, cancer_info: Optional[str]) -> str:
    """
    AI API 호출 실패 시 반환할 폴백 응답입니다.
    공공 API 데이터가 있으면 그대로 보여주고, 없으면 기본 안내 메시지를 반환합니다.
    """
    if cancer_info:
        return (
            f"⚠️ AI 분석을 일시적으로 사용할 수 없습니다.\n\n"
            f"공공데이터 기반 참고 정보:\n{cancer_info}\n\n"
            f"정확한 진단은 반드시 전문의에게 받으시기 바랍니다."
        )
    return (
        "⚠️ 현재 AI 분석 서비스를 일시적으로 사용할 수 없습니다. "
        "정확한 진단은 반드시 전문의에게 받으시기 바랍니다."
    )
