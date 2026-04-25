"""
services/vector_service.py
---------------------------
ChromaDB를 이용한 벡터 유사도 검색 서비스입니다.

동작 방식:
1. 앱 최초 실행 시 암 관련 기초 문서들을 ChromaDB에 임베딩하여 저장
2. 사용자 증상 입력 시 임베딩 변환 후 가장 유사한 문서 검색
3. 검색된 문서를 AI 프롬프트에 컨텍스트로 전달 (RAG 패턴)

임베딩 모델:
- sentence-transformers의 한국어 지원 모델 사용
- 'jhgan/ko-sroberta-multitask' : 한국어 특화 문장 임베딩 모델

주의: 첫 실행 시 모델 다운로드로 시간이 걸릴 수 있습니다 (약 400MB)
"""

import logging
from typing import Optional

import chromadb
from chromadb.utils import embedding_functions

from app.core import config

logger = logging.getLogger(__name__)

# ChromaDB 컬렉션 이름
COLLECTION_NAME = "cancer_symptom_docs"

# 한국어 임베딩 모델
# pip install sentence-transformers 필요
EMBEDDING_MODEL = "jhgan/ko-sroberta-multitask"

# 앱 시작 시 미리 저장해둘 암 증상 기초 문서들
# 실제 서비스에서는 국가암정보센터 데이터를 파싱해서 대량으로 넣는 것을 권장합니다
SEED_DOCUMENTS = [
    {
        "id": "lung_symptom_1",
        "text": "폐암의 주요 증상: 3주 이상 지속되는 기침, 피가 섞인 가래(혈담), 숨 가쁨, 흉통, 쉰 목소리, 체중 감소, 식욕 부진이 나타날 수 있습니다.",
        "metadata": {"cancer_type": "폐암", "info_type": "증상"}
    },
    {
        "id": "colon_symptom_1",
        "text": "대장암의 주요 증상: 혈변(대변에 피가 섞임), 배변 습관 변화, 복통, 복부 팽만감, 잦은 설사 또는 변비, 체중 감소, 빈혈이 나타날 수 있습니다.",
        "metadata": {"cancer_type": "대장암", "info_type": "증상"}
    },
    {
        "id": "stomach_symptom_1",
        "text": "위암의 주요 증상: 소화불량, 위 부위의 불편감, 식후 포만감, 구역질, 체중 감소, 흑색변, 피를 토하는 증상이 나타날 수 있습니다.",
        "metadata": {"cancer_type": "위암", "info_type": "증상"}
    },
    {
        "id": "liver_symptom_1",
        "text": "간암의 주요 증상: 오른쪽 상복부 통증, 복부 팽만, 황달(눈과 피부가 노래짐), 체중 감소, 식욕 부진, 피로감이 나타날 수 있습니다.",
        "metadata": {"cancer_type": "간암", "info_type": "증상"}
    },
    {
        "id": "breast_symptom_1",
        "text": "유방암의 주요 증상: 유방의 멍울(혹), 유두 분비물, 유방 피부 변화(오렌지 껍질 모양), 유두 함몰, 겨드랑이 림프절 종대가 나타날 수 있습니다.",
        "metadata": {"cancer_type": "유방암", "info_type": "증상"}
    },
    {
        "id": "cervical_symptom_1",
        "text": "자궁경부암의 주요 증상: 비정상적인 질 출혈(성교 후, 월경 사이, 폐경 후), 질 분비물 증가, 골반통이 나타날 수 있습니다.",
        "metadata": {"cancer_type": "자궁경부암", "info_type": "증상"}
    },
    {
        "id": "pancreatic_symptom_1",
        "text": "췌장암의 주요 증상: 황달, 등 쪽으로 퍼지는 복통, 체중 감소, 식욕 부진, 소화 장애, 당뇨 갑작스러운 발병이 나타날 수 있습니다.",
        "metadata": {"cancer_type": "췌장암", "info_type": "증상"}
    },
    {
        "id": "thyroid_symptom_1",
        "text": "갑상선암의 주요 증상: 목 앞부분의 혹(결절), 목소리 변화(쉰 목소리), 연하 곤란(삼킴 어려움), 목 림프절 종대가 나타날 수 있습니다.",
        "metadata": {"cancer_type": "갑상선암", "info_type": "증상"}
    },
]


def _get_chroma_collection():
    """
    ChromaDB 클라이언트와 컬렉션을 초기화합니다.
    persist_directory를 설정해서 앱을 재시작해도 데이터가 유지됩니다.
    """
    try:
        # 로컬 디스크에 영구 저장
        client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)

        # 한국어 임베딩 함수 설정
        # SentenceTransformerEmbeddingFunction은 로컬에서 임베딩을 생성합니다 (API 비용 없음)
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )

        # 컬렉션이 없으면 생성, 있으면 가져옴
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"}  # 코사인 유사도 사용
        )

        return collection

    except Exception as e:
        logger.error(f"ChromaDB 초기화 실패: {e}")
        return None


def initialize_vector_db() -> None:
    """
    앱 시작 시 호출하는 초기화 함수입니다.
    컬렉션이 비어있으면 기초 문서(SEED_DOCUMENTS)를 임베딩해서 저장합니다.
    이미 데이터가 있으면 스킵합니다.
    """
    collection = _get_chroma_collection()
    if collection is None:
        logger.warning("ChromaDB 초기화 실패 - 벡터 검색 기능 비활성화")
        return

    # 이미 데이터가 있으면 중복 저장 방지
    existing_count = collection.count()
    if existing_count > 0:
        logger.info(f"ChromaDB 이미 초기화됨 (문서 수: {existing_count})")
        return

    # 기초 문서 일괄 저장
    collection.add(
        ids=[doc["id"] for doc in SEED_DOCUMENTS],
        documents=[doc["text"] for doc in SEED_DOCUMENTS],
        metadatas=[doc["metadata"] for doc in SEED_DOCUMENTS],
    )
    logger.info(f"ChromaDB 초기화 완료: {len(SEED_DOCUMENTS)}개 문서 저장")


def search_similar_symptoms(symptom: str, n_results: int = 3) -> Optional[str]:
    """
    사용자 증상과 의미적으로 가장 유사한 문서를 검색합니다.

    Args:
        symptom: 사용자가 입력한 증상 텍스트
        n_results: 반환할 문서 수 (기본 3개)

    Returns:
        검색된 문서들을 하나의 문자열로 합쳐서 반환
        실패 시 None 반환
    """
    collection = _get_chroma_collection()
    if collection is None:
        return None

    try:
        results = collection.query(
            query_texts=[symptom],
            n_results=n_results,
            # 유사도 점수도 함께 반환
            include=["documents", "metadatas", "distances"]
        )

        if not results["documents"] or not results["documents"][0]:
            return None

        # 검색 결과를 읽기 쉬운 텍스트로 포맷팅
        formatted_parts = []
        for i, (doc, meta, distance) in enumerate(zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        )):
            # distance가 낮을수록 유사도가 높음 (cosine distance)
            similarity_pct = round((1 - distance) * 100, 1)
            cancer_type = meta.get("cancer_type", "미상")
            formatted_parts.append(
                f"[유사 문서 {i+1}] 암종: {cancer_type} (유사도: {similarity_pct}%)\n{doc}"
            )

        result_text = "\n\n".join(formatted_parts)
        logger.info(f"벡터 검색 완료: {len(formatted_parts)}개 문서 반환")
        return result_text

    except Exception as e:
        logger.error(f"벡터 검색 실패: {e}")
        return None