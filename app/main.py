from fastapi import FastAPI

from app.apis import auth
from app.db.database import initialize_tortoise

app = FastAPI(title="DiagnoseMe", version="0.1.0", redirect_slashes=False)
app.include_router(auth.router)

# Tortoise ORM이 초기화 후 FastAPI와 연결
initialize_tortoise(app)


@app.get("/")
async def root():
    return {"message": "Hello World"}
