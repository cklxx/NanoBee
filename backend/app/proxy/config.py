"""Configuration for the Claude proxy (OpenAI-compatible bridge)."""
from __future__ import annotations

import os
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict


class ProxyConfig(BaseSettings):
    """Environment-driven settings used by the proxy router."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    azure_api_version: str | None = None
    request_timeout: int = 90
    max_tokens_limit: int = 4096
    min_tokens_limit: int = 100

    big_model: str = "gpt-4o"
    middle_model: str = "gpt-4o"
    small_model: str = "gpt-4o-mini"

    anthropic_api_key: str = ""
    log_level: str = "INFO"

    def validate_client_api_key(self, candidate: str | None) -> bool:
        """Validate client-provided Anthropic key when configured."""

        if not self.anthropic_api_key:
            return True
        return bool(candidate) and candidate == self.anthropic_api_key

    def get_custom_headers(self) -> dict[str, str]:
        """Collect headers from ``CUSTOM_HEADER_*`` env vars."""

        headers: dict[str, str] = {}
        for key, value in os.environ.items():
            if key.startswith("CUSTOM_HEADER_"):
                header_name = key[len("CUSTOM_HEADER_") :].replace("_", "-")
                if header_name:
                    headers[header_name] = value
        return headers


proxy_config = ProxyConfig()
