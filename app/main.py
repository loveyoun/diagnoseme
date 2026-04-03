from fastapi import FastAPI

from app.apis import appointment, auth, user
from app.core import config
from app.db.database import initialize_tortoise

# DEBUG 모드일때만 /docs 확인 가능
# load_dotenv()
# DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
app: FastAPI = FastAPI(title="DiagnoseMe", version="0.1.0", redirect_slashes=False,
                       docs_url="/docs" if config.DEBUG else None)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(appointment.router)

# Tortoise ORM이 초기화 후 FastAPI와 연결
initialize_tortoise(app)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World"}
