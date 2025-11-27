from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = Field(
        default=f"sqlite:///{Path(__file__).resolve().parent.parent / 'data.db'}",
        description="SQLAlchemy database URL",
    )
    openai_api_key: str | None = Field(default=None, description="OpenAI API key (optional)")
    openai_base_url: str | None = Field(
        default=None, description="Base URL for the OpenAI-compatible API"
    )
    openai_model: str = Field(default="gpt-4o-mini", description="LLM model to use")
    workspaces_root: Path = Field(
        default=Path("/workspace/NanoBee/workspaces"),
        description="Root directory where task workspaces are stored",
    )

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:3001"],
        description="Allowed CORS origins for the API",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: list[str] | str | None) -> list[str]:
        """Allow comma-separated strings in env for convenience."""

        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    model_config = {
        "env_prefix": "NANOBEE_",
        "env_file": ".env",
        "case_sensitive": False,
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
