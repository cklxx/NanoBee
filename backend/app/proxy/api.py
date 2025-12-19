"""FastAPI router implementing the Claude Code proxy endpoints."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from .client import openai_client
from .config import proxy_config
from .conversion.request_converter import convert_claude_to_openai
from .conversion.response_converter import convert_openai_streaming_to_claude, convert_openai_to_claude_response
from .model_manager import model_manager
from .models.claude import ClaudeMessagesRequest, ClaudeTokenCountRequest

router = APIRouter()
logger = logging.getLogger(__name__)


def validate_api_key(x_api_key: Optional[str] = Header(None), authorization: Optional[str] = Header(None)):
    client_api_key = None
    if x_api_key:
        client_api_key = x_api_key
    elif authorization and authorization.startswith("Bearer "):
        client_api_key = authorization.replace("Bearer ", "")

    if not proxy_config.anthropic_api_key:
        return
    if not proxy_config.validate_client_api_key(client_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key. Please provide a valid Anthropic API key.")


@router.post("/v1/messages")
async def create_message(request: ClaudeMessagesRequest, http_request: Request, _: None = Depends(validate_api_key)):
    if not proxy_config.openai_api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is required for proxy usage")

    request_id = str(uuid.uuid4())
    openai_request = convert_claude_to_openai(request, model_manager)
    if await http_request.is_disconnected():
        raise HTTPException(status_code=499, detail="Client disconnected")

    if request.stream:
        try:
            openai_stream = openai_client.create_chat_completion_stream(openai_request, request_id)
            return StreamingResponse(
                convert_openai_streaming_to_claude(openai_stream, request, logger=logger),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*",
                },
            )
        except HTTPException as exc:
            error_message = openai_client.classify_openai_error(exc.detail)
            error_response = {"type": "error", "error": {"type": "api_error", "message": error_message}}
            return JSONResponse(status_code=exc.status_code, content=error_response)
    openai_response = await openai_client.create_chat_completion(openai_request, request_id)
    return convert_openai_to_claude_response(openai_response, request)


@router.post("/v1/messages/count_tokens")
async def count_tokens(request: ClaudeTokenCountRequest, _: None = Depends(validate_api_key)):
    total_chars = 0
    if request.system:
        if isinstance(request.system, str):
            total_chars += len(request.system)
        elif isinstance(request.system, list):
            for block in request.system:
                if hasattr(block, "text") and block.text is not None:
                    total_chars += len(block.text)

    for msg in request.messages:
        if msg.content is None:
            continue
        if isinstance(msg.content, str):
            total_chars += len(msg.content)
        elif isinstance(msg.content, list):
            for block in msg.content:
                if hasattr(block, "text") and block.text is not None:
                    total_chars += len(block.text)

    estimated_tokens = max(1, total_chars // 4)
    return {"input_tokens": estimated_tokens}


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "openai_api_configured": bool(proxy_config.openai_api_key),
        "api_key_valid": bool(proxy_config.openai_api_key),
        "client_api_key_validation": bool(proxy_config.anthropic_api_key),
    }


@router.get("/test-connection")
async def test_connection():
    if not proxy_config.openai_api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is required for proxy usage")

    try:
        test_response = await openai_client.create_chat_completion(
            {"model": proxy_config.small_model, "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 5}
        )
        return {
            "status": "success",
            "message": "Successfully connected to OpenAI API",
            "model_used": proxy_config.small_model,
            "timestamp": datetime.now().isoformat(),
            "response_id": test_response.get("id", "unknown"),
        }
    except Exception as exc:  # pragma: no cover - defensive
        return JSONResponse(status_code=503, content={"status": "error", "message": str(exc)})
