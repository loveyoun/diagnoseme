from pydantic import BaseModel, Field


class SymptomRequest(BaseModel):
    """
    사용자가 Swagger의 Request Body에 입력하는 모델
    """
    symptom: str = Field(
        ...,
        min_length=2,
        max_length=2000,
        description="사용자가 입력하는 증상 텍스트",
        examples=["3개월째 기침이 멈추지 않고, 가끔 피가 섞인 가래가 나옵니다."]
    )
    # 선택 입력: 나이, 성별을 주면 AI 분석이 더 정확해집니다
    age: int | None = Field(
        None,
        ge=0,
        le=120,
        description="나이 (선택 입력)",
        examples=[45]
    )
    gender: str | None = Field(
        None,
        pattern="^(남|여)$",
        description="성별: '남' 또는 '여' (선택 입력)",
        examples=["남"]
    )


class CancerApiData(BaseModel):
    """
    공공 API에서 수집한 암 관련 데이터를 담는 중간 모델
    서비스 레이어에서 채워서 AI 서비스로 전달
    """
    # 국가암정보센터 - 암종별 증상/진단/치료 정보
    cancer_info: str | None = Field(None, description="암종 기본 정보 및 증상")
    # 국립암센터 - 암 발생률 통계
    cancer_stats: str | None = Field(None, description="암종별 발생률 통계")
    # 벡터 DB에서 검색된 유사 증상 문서
    similar_cases: str | None = Field(None, description="유사 증상 관련 문서")
    # API 호출 중 발생한 에러 메시지 (부분 실패 허용)
    errors: list[str] = Field(default_factory=list, description="API 호출 에러 목록")


class SymptomResponse(BaseModel):
    """
    Swagger UI의 Response Body에 표시되는 최종 응답 모델
    """
    # 사용자가 입력한 원본 증상
    original_symptom: str = Field(..., description="사용자 입력 증상")

    # AI가 생성한 분석 결과
    ai_analysis: str = Field(..., description="AI 분석 결과")

    # Redis에서 캐시를 히트했는지 여부 (디버깅용)
    cache_hit: bool = Field(False, description="Redis 캐시에서 응답했는지 여부")

    # 어떤 공공 API 데이터를 활용했는지 (디버깅용)
    data_sources_used: list[str] = Field(
        default_factory=list,
        description="데이터 수집에 성공한 API 목록"
    )

    # 주의사항: 의학적 판단이 아님을 명시
    disclaimer: str = Field(
        default="본 정보는 참고용이며, 정확한 진단은 반드시 전문의에게 받으시기 바랍니다.",
        description="의료 면책 문구"
    )
