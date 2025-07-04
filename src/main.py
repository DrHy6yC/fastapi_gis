import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from src.api.features import router as features_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(features_router)


if __name__ == "__main__":
    uvicorn.run(app="main:app", reload=True)
