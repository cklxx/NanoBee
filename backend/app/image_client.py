"""HTTP client for calling the slide image generation LLM API."""
from __future__ import annotations

from typing import Any

import httpx

from .config import settings


class ImageGenerationClient:
    """Small wrapper around the upstream image LLM endpoint."""

    def __init__(self) -> None:
        self.base_url = settings.image_api_base_url.rstrip("/")
        self.path = settings.image_api_path
        self.model = settings.image_model
        self.api_key = settings.image_api_key

    @property
    def endpoint(self) -> str:
        return f"{self.base_url}/{self.path.lstrip('/')}"

    async def generate_images(self, prompts: list[str]) -> list[dict[str, Any]]:
        """Generate PPT visuals for each prompt.

        The method is intentionally defensive because upstream implementations
        may differ. It returns the raw provider payload alongside a stabilized
        ``url`` field if available.
        """

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        results: list[dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=60) as client:
            for prompt in prompts:
                payload = {"prompt": prompt, "model": self.model, "size": "1280x720"}
                response = await client.post(self.endpoint, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                url = self._extract_image_url(data)
                results.append({"prompt": prompt, "url": url, "raw": data})
        return results

    @staticmethod
    def _extract_image_url(payload: dict[str, Any]) -> str | None:
        """Best-effort extraction of an image URL from common API shapes."""

        if "url" in payload:
            return str(payload["url"])
        if isinstance(payload.get("data"), list) and payload["data"]:
            first = payload["data"][0]
            for key in ("url", "image_url", "src"):
                if key in first:
                    return str(first[key])
        if "image_url" in payload:
            return str(payload["image_url"])
        return None


def build_slide_prompts(topic: str, narrative: str | None, slide_count: int) -> list[str]:
    """Create image-friendly prompts for each slide."""

    prompts: list[str] = []
    for idx in range(slide_count):
        prompts.append(
            (
                f"Slide {idx + 1}: {topic}. "
                f"视觉风格: 扁平化演示风格，内容导向。 "
                f"叙述: {narrative or '突出关键信息，保持高对比度和可读性。'}"
            ).strip()
        )
    return prompts
