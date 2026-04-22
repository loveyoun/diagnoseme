from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.apis import appointment, auth, user, slot
from app.core import config, redis_client
from app.db.database import initialize_tortoise
from redis.asyncio import Redis


# DEBUG 모드일때만 /docs 확인 가능
# load_dotenv()
# DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
app: FastAPI = FastAPI(title="DiagnoseMe", version="0.1.0", redirect_slashes=False,
                       docs_url="/docs" if config.DEBUG else None)

@asynccontextmanager
async def lifespan(app:FastAPI):
    app.state.redis = redis_client
    yield
    await app.state.redis.close()  # 앱 종료 시 정리

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(appointment.router)
app.include_router(slot.router)

# Tortoise ORM이 초기화 후 FastAPI와 연결
initialize_tortoise(app)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "DiagnoseMe"}
