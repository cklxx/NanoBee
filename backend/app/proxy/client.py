"""OpenAI-compatible client with cancellation and error handling."""
from __future__ import annotations

import asyncio
import contextlib
import json
from typing import Any, AsyncGenerator, Dict, Optional

from fastapi import HTTPException
from openai import AsyncAzureOpenAI, AsyncOpenAI
from openai._exceptions import APIError, AuthenticationError, BadRequestError, RateLimitError

from .config import proxy_config


class OpenAIClient:
    def __init__(self) -> None:
        headers = {"Content-Type": "application/json", **proxy_config.get_custom_headers()}
        if proxy_config.azure_api_version:
            self.client = AsyncAzureOpenAI(
                api_key=proxy_config.openai_api_key,
                azure_endpoint=proxy_config.openai_base_url,
                api_version=proxy_config.azure_api_version,
                timeout=proxy_config.request_timeout,
                default_headers=headers,
            )
        else:
            self.client = AsyncOpenAI(
                api_key=proxy_config.openai_api_key,
                base_url=proxy_config.openai_base_url,
                timeout=proxy_config.request_timeout,
                default_headers=headers,
            )
        self.active_requests: Dict[str, asyncio.Event] = {}

    async def create_chat_completion(self, request: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        cancel_event = None
        if request_id:
            cancel_event = asyncio.Event()
            self.active_requests[request_id] = cancel_event

        try:
            completion_task = asyncio.create_task(self.client.chat.completions.create(**request))
            if cancel_event:
                cancel_task = asyncio.create_task(cancel_event.wait())
                done, pending = await asyncio.wait([completion_task, cancel_task], return_when=asyncio.FIRST_COMPLETED)
                for task in pending:
                    task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await task
                if cancel_task in done:
                    completion_task.cancel()
                    raise HTTPException(status_code=499, detail="Request cancelled by client")
                completion = await completion_task
            else:
                completion = await completion_task
            return completion.model_dump()
        except AuthenticationError as exc:
            raise HTTPException(status_code=401, detail=self.classify_openai_error(str(exc)))
        except RateLimitError as exc:
            raise HTTPException(status_code=429, detail=self.classify_openai_error(str(exc)))
        except BadRequestError as exc:
            raise HTTPException(status_code=400, detail=self.classify_openai_error(str(exc)))
        except APIError as exc:
            status_code = getattr(exc, "status_code", 500)
            raise HTTPException(status_code=status_code, detail=self.classify_openai_error(str(exc)))
        except Exception as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc
        finally:
            if request_id:
                self.active_requests.pop(request_id, None)

    async def create_chat_completion_stream(
        self, request: Dict[str, Any], request_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        cancel_event = None
        if request_id:
            cancel_event = asyncio.Event()
            self.active_requests[request_id] = cancel_event

        try:
            request["stream"] = True
            request.setdefault("stream_options", {})["include_usage"] = True
            streaming_completion = await self.client.chat.completions.create(**request)
            async for chunk in streaming_completion:
                if cancel_event and cancel_event.is_set():
                    raise HTTPException(status_code=499, detail="Request cancelled by client")
                chunk_json = json.dumps(chunk.model_dump(), ensure_ascii=False)
                yield f"data: {chunk_json}"
            yield "data: [DONE]"
        except AuthenticationError as exc:
            raise HTTPException(status_code=401, detail=self.classify_openai_error(str(exc)))
        except RateLimitError as exc:
            raise HTTPException(status_code=429, detail=self.classify_openai_error(str(exc)))
        except BadRequestError as exc:
            raise HTTPException(status_code=400, detail=self.classify_openai_error(str(exc)))
        except APIError as exc:
            status_code = getattr(exc, "status_code", 500)
            raise HTTPException(status_code=status_code, detail=self.classify_openai_error(str(exc)))
        except Exception as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc
        finally:
            if request_id:
                self.active_requests.pop(request_id, None)

    def classify_openai_error(self, error_detail: Any) -> str:
        error_str = str(error_detail).lower()
        if "unsupported_country_region_territory" in error_str or "country, region, or territory not supported" in error_str:
            return "OpenAI API is not available in your region. Consider using a VPN or Azure OpenAI service."
        if "invalid_api_key" in error_str or "unauthorized" in error_str:
            return "Invalid API key. Please check your OPENAI_API_KEY configuration."
        if "rate_limit" in error_str or "quota" in error_str:
            return "Rate limit exceeded. Please wait and try again, or upgrade your API plan."
        if "model" in error_str and ("not found" in error_str or "does not exist" in error_str):
            return "Model not found. Please check your BIG_MODEL and SMALL_MODEL configuration."
        if "billing" in error_str or "payment" in error_str:
            return "Billing issue. Please check your OpenAI account billing status."
        return str(error_detail)

    def cancel_request(self, request_id: str) -> bool:
        if request_id in self.active_requests:
            self.active_requests[request_id].set()
            return True
        return False


openai_client = OpenAIClient()
