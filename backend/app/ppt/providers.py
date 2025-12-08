from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class ImageResult:
    url: str
    data_url: str | None = None


@dataclass
class DoubaoTextProvider:
    """Lightweight client for Volcengine Doubao chat completions."""

    model: str
    base_url: str
    api_key: str | None = None
    client: httpx.Client | None = None

    @property
    def can_call(self) -> bool:
        return bool(self.api_key) and self._valid_url(self.base_url)

    def generate(self, prompt: str, stream: bool = False) -> str:
        if not self.api_key:
            raise RuntimeError("DoubaoTextProvider requires api_key to call")
        if not self._valid_url(self.base_url):
            raise RuntimeError("DoubaoTextProvider requires a valid base_url (http/https)")

        # 确保使用完整的端点URL
        url = self.base_url
        if not url.endswith("/chat/completions"):
            url = f"{url.rstrip('/')}/chat/completions"

        preview = self._prompt_preview(prompt)
        print(f"[Doubao] Attempting text generation | model={self.model} base_url={url} stream={stream} prompt_preview={preview}")

        with self._client() as client:
            response = client.post(
                url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 8192,  # 设置为8K，平衡质量和速度（官方最大支持32K）
                    "stream": stream,  # Enable streaming
                },
                timeout=120,  # 增加超时时间到120秒，大纲生成可能需要更长时间
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                detail = exc.response.text if exc.response is not None else ""
                print(f"[Doubao] HTTP {exc.response.status_code if exc.response else '?'} error: {detail}")
                raise
            
            if stream:
                # Stream mode: collect chunks
                content = ""
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data.get("choices", [{}])[0].get("delta", {})
                            chunk = delta.get("content", "")
                            if chunk:
                                content += chunk
                        except json.JSONDecodeError:
                            continue
                
                print(f"[Doubao] Streaming complete | total_length={len(content)}")
                return content
            else:
                # Non-stream mode: parse JSON response
                data = response.json()
                content = self._extract_content(data)
                print(f"[Doubao] Text generation succeeded | model={self.model} preview={content[:80].replace(chr(10), ' ')}")
                return content

    def _extract_content(self, data: dict[str, Any]) -> str:
        choices = data.get("choices") or []
        if not choices:
            raise ValueError("No choices returned from Doubao API")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if not content:
            raise ValueError("Missing message content from Doubao API")
        return str(content)

    @staticmethod
    def _prompt_preview(prompt: str) -> str:
        single_line = prompt.replace("\n", " ").strip()
        return (single_line[:120] + "...") if len(single_line) > 120 else single_line

    def _client(self) -> httpx.Client:
        if self.client:
            return self.client
        return httpx.Client()

    @staticmethod
    def _valid_url(url: str | None) -> bool:
        return bool(url) and str(url).startswith(("http://", "https://"))


@dataclass
class SeaDreamImageProvider:
    """Client for SeaDream image generation compatible endpoints."""

    model: str
    base_url: str
    api_key: str | None = None
    client: httpx.Client | None = None

    @property
    def can_call(self) -> bool:
        return bool(self.api_key) and self._valid_url(self.base_url)

    def generate(self, prompt: str, watermark: bool) -> ImageResult:
        if not self.api_key:
            raise RuntimeError("SeaDreamImageProvider requires api_key to call")
        if not self._valid_url(self.base_url):
            raise RuntimeError("SeaDreamImageProvider requires a valid base_url (http/https)")

        url = self._ensure_image_endpoint(self.base_url)

        payload = {
            "model": self.model,
            "prompt": prompt,
            # SeaDream requires the generated image to be at least 3,686,400 pixels.
            # Use a 16:9 size that meets the minimum to avoid 400 errors.
            "size": "2560x1440",
            "n": 1,
            # Prefer URL response to reduce payload size; fallback to b64 if URL missing.
            "response_format": "url",
            "watermark": watermark,
            "sequential_image_generation": "disabled",
            "stream": False,
        }

        with self._client() as client:
            try:
                response = client.post(
                    url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=payload,
                    timeout=120,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                detail = exc.response.text if exc.response is not None else ""
                print(f"[SeaDream] HTTP {exc.response.status_code if exc.response else '?'} error: {detail}")
                raise

            data = response.json()
            return self._extract_image_result(data)

    def _extract_image_result(self, data: dict[str, Any]) -> ImageResult:
        images = data.get("data") or []
        if not images:
            raise ValueError("No image data returned from SeaDream API")
        payload = images[0]
        url = payload.get("url")
        if url:
            return ImageResult(url=url, data_url=None)
        b64 = payload.get("b64_json")
        if not b64:
            raise ValueError("Missing url or b64_json in SeaDream response")
        data_url = f"data:image/png;base64,{b64}"
        return ImageResult(url=data_url, data_url=data_url)

    def _client(self) -> httpx.Client:
        if self.client:
            return self.client
        return httpx.Client()

    @staticmethod
    def _valid_url(url: str | None) -> bool:
        return bool(url) and str(url).startswith(("http://", "https://"))

    @staticmethod
    def _ensure_image_endpoint(url: str) -> str:
        """Append images/generations if caller passed the API root."""
        trimmed = url.rstrip("/")
        if trimmed.endswith("/images/generations"):
            return trimmed
        return f"{trimmed}/images/generations"
