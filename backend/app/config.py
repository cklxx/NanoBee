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

    model_config = SettingsConfigDict(env_prefix="NANOBEE_", env_file=".env", env_file_encoding="utf-8", extra="ignore")

    claude_api_key: str = Field(
        default="",
        description="API key for Claude / Anthropic service",
        alias="ANTHROPIC_API_KEY",
    )
    anthropic_base_url: str = Field(
        default="",
        description="Override base URL for Anthropic-compatible endpoints",
        alias="ANTHROPIC_BASE_URL",
    )
    text_api_key: str = Field(
        default="",
        description="API key for text model providers (proxy friendly)",
        alias="TEXT_API_KEY",
    )
    default_text_base_url: str = Field(
        default="",
        description="Base URL for Claude-compatible text generation service",
        alias="DEFAULT_TEXT_BASE_URL",
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

    openai_api_key: str = Field(
        default="",
        description="API key for OpenAI-compatible backends (for proxy)",
        alias="OPENAI_API_KEY",
    )
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        description="Base URL for OpenAI-compatible chat completions",
        alias="OPENAI_BASE_URL",
    )
    openai_big_model: str = Field(default="gpt-4o", description="Primary OpenAI model", alias="OPENAI_BIG_MODEL")
    openai_middle_model: str = Field(default="gpt-4o", description="Secondary OpenAI model", alias="OPENAI_MIDDLE_MODEL")
    openai_small_model: str = Field(default="gpt-4o-mini", description="Lightweight OpenAI model", alias="OPENAI_SMALL_MODEL")

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

        effective_key = self.text_api_key or self.claude_api_key
        if effective_key and not os.environ.get("ANTHROPIC_API_KEY"):
            os.environ["ANTHROPIC_API_KEY"] = effective_key
        if self.anthropic_base_url and not os.environ.get("ANTHROPIC_BASE_URL"):
            os.environ["ANTHROPIC_BASE_URL"] = self.anthropic_base_url
        elif self.default_text_base_url and not os.environ.get("ANTHROPIC_BASE_URL"):
            os.environ["ANTHROPIC_BASE_URL"] = self.default_text_base_url
        if self.openai_api_key and not os.environ.get("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = self.openai_api_key
        if self.openai_base_url and not os.environ.get("OPENAI_BASE_URL"):
            os.environ["OPENAI_BASE_URL"] = self.openai_base_url
        if self.openai_big_model and not os.environ.get("OPENAI_BIG_MODEL"):
            os.environ["OPENAI_BIG_MODEL"] = self.openai_big_model
        if self.openai_middle_model and not os.environ.get("OPENAI_MIDDLE_MODEL"):
            os.environ["OPENAI_MIDDLE_MODEL"] = self.openai_middle_model
        if self.openai_small_model and not os.environ.get("OPENAI_SMALL_MODEL"):
            os.environ["OPENAI_SMALL_MODEL"] = self.openai_small_model


settings = Settings()
settings.apply_environment()
