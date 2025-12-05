from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the PPT workflow API."""

    model_config = SettingsConfigDict(
        env_prefix="NANOBEE_",
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    default_text_model: str = Field(
        default="doubao-seed-1-6-251015",
        description="Default text model for PPT workflow",
    )
    default_text_base_url: str = Field(
        default="https://ark.cn-beijing.volces.com/api/v3",
        description="Default text model base URL",
    )
    text_api_key: str | None = Field(
        default=None,
        description="API key for calling the default text model provider",
    )
    default_image_model: str = Field(
        default="doubao-seedream-4-5-251128",
        description="Default image model for PPT workflow",
    )
    default_image_base_url: str = Field(
        default="https://ark.cn-beijing.volces.com/api/v3",
        description="Default image model base URL (root; images endpoint appended automatically)",
    )
    image_api_key: str | None = Field(
        default=None,
        description="API key for calling the default image model provider",
    )
    allow_image_watermark: bool = Field(
        default=False,
        description="Whether downstream image generation should add AI watermarks (disabled by default).",
    )
    workspaces_root: Path = Field(
        default=Path("./workspaces"),
        description="Root directory where prompt notebooks and artifacts are stored",
    )

    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:3001,http://localhost,http://127.0.0.1:3000,http://127.0.0.1:3001",
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
