from __future__ import annotations

from collections.abc import Generator

from fastapi import HTTPException

from .config import get_settings
from .db.session import SessionLocal
from .llm.base import LLMClient
from .llm.dummy import DummyLLM
from .llm.openai_client import OpenAIClient


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_llm_client() -> LLMClient:
    settings = get_settings()
    if settings.openai_api_key:
        return OpenAIClient(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            base_url=settings.openai_base_url,
        )
    if settings.allow_dummy_llm:
        return DummyLLM()
    raise HTTPException(
        status_code=503,
        detail="LLM is not configured. Set NANOBEE_OPENAI_API_KEY (and optional NANOBEE_OPENAI_BASE_URL) "
        "or enable dummy mode with NANOBEE_ALLOW_DUMMY_LLM=1 for local demos.",
    )
