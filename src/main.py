import sys

from pathlib import Path

from src.config import settings

sys.path.append(str(Path(__file__).parent.parent))

from contextlib import asynccontextmanager

import uvicorn

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from src.api.features import router as features_router
from src.api.stats import router as stats_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(lifespan=lifespan, root_path=settings.ROOT_PATH)

app.include_router(features_router)
app.include_router(stats_router)

app.mount(f"/static", StaticFiles(directory="src/static"), name="static")


if __name__ == "__main__":
    uvicorn.run(app="main:app", reload=True)
