from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class DoubaoTextProvider:
    """Lightweight client for Volcengine Doubao chat completions."""

    model: str
    base_url: str
    api_key: str | None = None
    client: httpx.Client | None = None

    @property
    def can_call(self) -> bool:
        return bool(self.api_key)

    def generate(self, prompt: str) -> str:
        if not self.can_call:
            raise RuntimeError("DoubaoTextProvider requires api_key to call")

        # 确保使用完整的端点URL
        url = self.base_url
        if not url.endswith("/chat/completions"):
            url = f"{url.rstrip('/')}/chat/completions"

        with self._client() as client:
            response = client.post(
                url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": prompt},
                    ],
                },
                timeout=60,  # 增加超时时间到60秒
            )
            response.raise_for_status()
            data = response.json()
            return self._extract_content(data)

    def _extract_content(self, data: dict[str, Any]) -> str:
        choices = data.get("choices") or []
        if not choices:
            raise ValueError("No choices returned from Doubao API")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if not content:
            raise ValueError("Missing message content from Doubao API")
        return str(content)

    def _client(self) -> httpx.Client:
        if self.client:
            return self.client
        return httpx.Client()


@dataclass
class SeaDreamImageProvider:
    """Client for SeaDream image generation compatible endpoints."""

    model: str
    base_url: str
    api_key: str | None = None
    client: httpx.Client | None = None

    @property
    def can_call(self) -> bool:
        return bool(self.api_key)

    def generate(self, prompt: str, watermark: bool) -> str:
        if not self.can_call:
            raise RuntimeError("SeaDreamImageProvider requires api_key to call")

        with self._client() as client:
            response = client.post(
                self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "size": "1024x576",
                    "n": 1,
                    "response_format": "b64_json",
                    "watermark": watermark,
                },
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
            return self._extract_data_url(data)

    def _extract_data_url(self, data: dict[str, Any]) -> str:
        images = data.get("data") or []
        if not images:
            raise ValueError("No image data returned from SeaDream API")
        payload = images[0]
        b64 = payload.get("b64_json")
        if not b64:
            raise ValueError("Missing b64_json in SeaDream response")
        return f"data:image/png;base64,{b64}"

    def _client(self) -> httpx.Client:
        if self.client:
            return self.client
        return httpx.Client()
