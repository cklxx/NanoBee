from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import logs, tasks, workspaces
from .db import models  # noqa: F401  # ensure models are registered with Base.metadata
from .db.base import Base
from .db.session import engine
from .config import get_settings

@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="NanoBee Harness", version="0.2.0", lifespan=lifespan)


settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(tasks.router)
app.include_router(workspaces.router)
app.include_router(logs.router)
