"""Configuration for the NanoBee agent backend.

This module centralizes environment-driven settings so that the agent
and skills can be configured without code changes. Settings are loaded
from environment variables prefixed with ``NANOBEE_`` to avoid collisions.
"""
from __future__ import annotations

import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="NANOBEE_", extra="ignore")

    claude_api_key: str = Field(
        default="",
        description="API key for Claude / Anthropic service",
        alias="ANTHROPIC_API_KEY",
    )
    default_text_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Claude model used for text-first agent orchestration",
    )
    system_prompt: str = Field(
        default=(
            "你是一个帮助用户规划并生成PPT的智能体，"
            "会主动调用工具获得大纲和生图能力，"
            "确保输出结构化、可执行的内容。"
        ),
        description="System prompt used for all agent conversations",
    )

    image_api_key: str = Field(
        default="",
        description="API key for the image generation LLM service",
        alias="IMAGE_LLM_API_KEY",
    )
    image_api_base_url: str = Field(
        default="https://api.example.com/v1",
        description="Base URL for the image generation LLM HTTP API",
    )
    image_api_path: str = Field(
        default="/images",
        description="Path for the image generation endpoint relative to the base URL",
    )
    image_model: str = Field(
        default="ppt-vision-pro",
        description="Model name for generating slide visuals",
    )
    default_slide_count: int = Field(
        default=6,
        description="Fallback number of slides when the user does not specify",
    )

    def apply_environment(self) -> None:
        """Apply settings to process environment for SDK compatibility."""

        if self.claude_api_key and not os.environ.get("ANTHROPIC_API_KEY"):
            os.environ["ANTHROPIC_API_KEY"] = self.claude_api_key


settings = Settings()
settings.apply_environment()
