from __future__ import annotations

from collections.abc import Generator

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
    return DummyLLM()
