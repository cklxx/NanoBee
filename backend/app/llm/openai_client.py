from __future__ import annotations

from typing import Any, Dict, List

import httpx

from .base import LLMClient, LLMMessage


class OpenAIClient(LLMClient):
    """Minimal OpenAI chat client using the HTTP API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: str | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or "https://api.openai.com/v1/chat/completions"

    async def chat(self, messages: List[LLMMessage], tools: list | None = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"model": self.model, "messages": messages}
        if tools:
            payload["tools"] = tools

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(self.base_url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            # Return the first choice content for compatibility with DummyLLM
            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})
            return {"content": message.get("content", ""), "raw": data}
