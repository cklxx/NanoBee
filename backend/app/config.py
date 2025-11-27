from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="NANOBEE_",
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

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

    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001",
        description="Allowed CORS origins for the API (comma-separated or JSON list)",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parsed CORS origins as a list regardless of input format."""

        raw_value = self.cors_origins.strip()
        try:
            loaded = json.loads(raw_value)
            if isinstance(loaded, list):
                return [str(item).strip() for item in loaded if str(item).strip()]
        except json.JSONDecodeError:
            pass

        normalized = raw_value
        if normalized.startswith("[") and normalized.endswith("]"):
            normalized = normalized[1:-1]
        return [item.strip() for item in normalized.split(",") if item.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
