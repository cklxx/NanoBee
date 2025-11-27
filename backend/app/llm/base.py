from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, TypedDict


class LLMMessage(TypedDict):
    role: str
    content: str


class LLMClient(ABC):
    @abstractmethod
    async def chat(self, messages: List[LLMMessage], tools: list | None = None) -> Dict[str, Any]:
        """Send chat messages to a model and return the raw response payload."""
        raise NotImplementedError
