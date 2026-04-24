from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import ConnectionPool
from redis.asyncio import Redis
from tortoise import Tortoise

from app.apis import appointment, auth, user, slot
from app.core import config
from app.db.database import TORTOISE_APP_MODELS, TORTOISE_ORM


# DEBUG 모드일때만 /docs 확인 가능
# load_dotenv()
# DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"


# 리소스 생성 시점을 lifespan 내부로 이동
# startup / shutdown lifecycle 관리
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- [START] 초기화 영역 ---

    # 1. Redis 초기화
    pool: ConnectionPool = ConnectionPool.from_url(  # Redis.from_url()
        f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}",
        password=str(config.REDIS_PASSWORD) if config.REDIS_PASSWORD is not None else None,
        max_connections=10,
        decode_responses=True,
    )
    app.state.redis = Redis(connection_pool=pool)

    # 2. Tortoise 초기화
    Tortoise.init_models(TORTOISE_APP_MODELS, "models")
    await Tortoise.init(config=TORTOISE_ORM)

    # 3. DB 연결 확인
    try:
        conn = Tortoise.get_connection("default")
        await conn.execute_query_dict("SELECT 1")
        print("✅ DB & Redis 연결 성공!")
    except Exception as e:
        print(f"❌ 초기화 중 오류 발생: {e}")
        raise e

    yield  # --- 앱 실행 중 ---

    # --- [END] 정리 영역 (앱 종료 시) ---

    # 1. Redis 종료
    await app.state.redis.aclose(close_connection_pool=True)
    # await pool.disconnect()  # 풀도 명시적으로 정리

    # 2. Tortoise 종료
    await Tortoise.close_connections()


app: FastAPI = FastAPI(title="DiagnoseMe",
                       version="0.1.0",
                       redirect_slashes=False,
                       docs_url="/docs" if config.DEBUG else None,
                       lifespan=lifespan)
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(appointment.router)
app.include_router(slot.router)


# Tortoise ORM 초기화 후 FastAPI와 연결
# initialize_tortoise(app)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello, DiagnoseMe!"}
