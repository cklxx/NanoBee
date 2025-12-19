"""Model mapping helpers for Claude -> OpenAI translation."""
from __future__ import annotations

from .config import proxy_config


class ModelManager:
    def __init__(self, config: proxy_config.__class__):
        self.config = config

    def map_claude_model_to_openai(self, claude_model: str) -> str:
        """Map Claude model naming to OpenAI-compatible alternatives."""

        model_lower = (claude_model or "").lower()
        if claude_model.startswith("gpt-") or claude_model.startswith("o1-"):
            return claude_model
        if claude_model.startswith("ep-") or claude_model.startswith("doubao-") or claude_model.startswith("deepseek-"):
            return claude_model

        if "haiku" in model_lower:
            return self.config.small_model
        if "sonnet" in model_lower:
            return self.config.middle_model
        if "opus" in model_lower:
            return self.config.big_model
        return self.config.big_model


model_manager = ModelManager(proxy_config)
