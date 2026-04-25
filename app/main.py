import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import ConnectionPool
from redis.asyncio import Redis
from tortoise import Tortoise

from app.apis import appointment, auth, user, slot, symptom
from app.core import config
from app.db.database import TORTOISE_APP_MODELS, TORTOISE_ORM

logger = logging.getLogger(__name__)


# DEBUG 모드일때만 /docs 확인 가능
# load_dotenv()
# DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

# 리소스 생성 시점을 lifespan 내부로 이동
# startup / shutdown lifecycle 관리
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    앱 시작/종료 시 실행할 작업을 정의합니다.
    FastAPI의 lifespan 이벤트 핸들러입니다.

    시작 시:
    - ChromaDB 벡터 DB 초기화 (기초 문서 임베딩 저장)

    종료 시:
    - 필요한 정리 작업 (현재는 없음)
    """

    # --- [START] 초기화 영역 ---
    logger.info("앱 시작: 초기화 중...")

    # 1. Redis 초기화
    pool: ConnectionPool = ConnectionPool.from_url(  # Redis.from_url()
        f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}",
        password=str(config.REDIS_PASSWORD) if config.REDIS_PASSWORD is not None else None,
        max_connections=10,
        decode_responses=True,
    )
    redis_client = Redis(connection_pool=pool)

    try:
        await redis_client.ping()
        logger.info("✅ Redis 연결 성공!")
        app.state.redis = redis_client
    except Exception as e:
        logger.warning(f"Redis 연결 실패 (캐시 없이 진행): {e}")

    # 2. Tortoise 초기화
    Tortoise.init_models(TORTOISE_APP_MODELS, "models")
    await Tortoise.init(config=TORTOISE_ORM)

    # 3. DB 연결 확인
    try:
        conn = Tortoise.get_connection("default")
        await conn.execute_query_dict("SELECT 1")
        logger.info("✅ DB 연결 성공!")
    except Exception as e:
        logger.warning(f"❌ DB 초기화 중 오류 발생: {e}")
        raise e

    # 동기 함수이므로 직접 호출 (임베딩 모델 로딩은 시간이 걸릴 수 있음)
    # initialize_vector_db()

    logger.info("초기화 완료. 서비스 준비됨.")
    yield  # --- 앱 실행 중 ---

    # --- [END] 정리 영역 (앱 종료 시) ---
    logger.info("앱 종료 중...")

    # 1. Redis 종료
    await app.state.redis.aclose(close_connection_pool=True)
    # await pool.disconnect()  # 풀도 명시적으로 정리

    # 2. Tortoise 종료
    await Tortoise.close_connections()


app: FastAPI = FastAPI(title="DiagnoseMe",
                       description="""
                       국립암센터 공공데이터와 Gemini AI를 활용한 암 관련 증상 분석 서비스입니다.    
                       
                       ## 주요 기능
                       - 사용자 증상 텍스트 입력
                       - 국립암센터 공공 API 3종 자동 조회
                       - Redis 캐싱으로 빠른 반복 응답
                       - ChromaDB 벡터 검색으로 유사 증상 문서 제공
                       - Gemini 2.5 Flash AI 종합 분석    
                       
                       ## ⚠️ 주의사항
                       본 서비스는 참고용 정보 제공 목적이며, 의학적 진단을 대체하지 않습니다.
                       """,
                       version="0.1.0",
                       redirect_slashes=False,
                       docs_url="/docs" if config.DEBUG else None,
                       lifespan=lifespan)
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(appointment.router)
app.include_router(slot.router)
app.include_router(symptom.router)


# Tortoise ORM 초기화 후 FastAPI와 연결
# initialize_tortoise(app)


@app.get("/health", tags=["헬스체크"])
async def health_check():
    """
    서비스 상태 확인용 엔드포인트
    """
    return {"status": "ok", "service": "암 증상 분석 DiagnoseMe"}
