from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.works import router as works_router
from app.database import Base, engine
from app.models.work import Work


@asynccontextmanager
async def lifespan(app: FastAPI):

    yield


app = FastAPI(
    title="OpenAlex Platform",
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(works_router)


@app.get("/")
def root():
    return {
        "message": "OpenAlex Platform is running"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }