"""Convert Anthropic Claude messages payloads into OpenAI-style chat completions."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from ..constants import Constants
from ..models.claude import ClaudeMessage, ClaudeMessagesRequest
from ..config import proxy_config

logger = logging.getLogger(__name__)


def _flatten_system_content(system: str | list[dict[str, Any]]) -> str:
    if isinstance(system, str):
        return system
    text_parts: list[str] = []
    for block in system:
        if isinstance(block, dict) and block.get("type") == Constants.CONTENT_TEXT:
            text_parts.append(str(block.get("text", "")))
    return "\n\n".join([part for part in text_parts if part])


def convert_claude_user_message(msg: ClaudeMessage) -> dict[str, Any]:
    if isinstance(msg.content, str):
        return {"role": Constants.ROLE_USER, "content": msg.content}

    content_parts: list[dict[str, Any]] = []
    for block in msg.content:
        if not hasattr(block, "type"):
            continue
        if block.type == Constants.CONTENT_TEXT:
            content_parts.append({"type": Constants.CONTENT_TEXT, "text": getattr(block, "text", "")})
        elif block.type == Constants.CONTENT_IMAGE:
            content_parts.append(
                {
                    "type": "image_url",
                    "image_url": {"url": block.source.get("data") or block.source.get("url", "")},
                }
            )
    if not content_parts:
        return {"role": Constants.ROLE_USER, "content": msg.content}
    return {"role": Constants.ROLE_USER, "content": content_parts}


def convert_claude_assistant_message(msg: ClaudeMessage) -> dict[str, Any]:
    if isinstance(msg.content, str):
        return {"role": Constants.ROLE_ASSISTANT, "content": msg.content}

    tool_calls: list[dict[str, Any]] = []
    text_content = None
    for block in msg.content:
        if not hasattr(block, "type"):
            continue
        if block.type == Constants.CONTENT_TEXT:
            text_content = getattr(block, "text", "")
        elif block.type == Constants.CONTENT_TOOL_USE:
            tool_calls.append(
                {
                    "id": block.id,
                    "type": Constants.TOOL_FUNCTION,
                    Constants.TOOL_FUNCTION: {"name": block.name, "arguments": json.dumps(block.input)},
                }
            )

    openai_message: dict[str, Any] = {"role": Constants.ROLE_ASSISTANT}
    if text_content is not None:
        openai_message["content"] = text_content
    if tool_calls:
        openai_message["tool_calls"] = tool_calls
    if "content" not in openai_message:
        openai_message["content"] = ""
    return openai_message


def convert_claude_tool_results(msg: ClaudeMessage) -> list[dict[str, Any]]:
    openai_messages: list[dict[str, Any]] = []
    if not isinstance(msg.content, list):
        return openai_messages

    for block in msg.content:
        if not hasattr(block, "type") or block.type != Constants.CONTENT_TOOL_RESULT:
            continue
        content_value = block.content
        if isinstance(content_value, str):
            parsed: Any = content_value
            try:
                parsed = json.loads(content_value)
            except json.JSONDecodeError:
                parsed = content_value
        else:
            parsed = content_value

        openai_messages.append(
            {
                "role": Constants.ROLE_TOOL,
                "tool_call_id": block.tool_use_id,
                "content": parsed,
            }
        )
    return openai_messages


def convert_claude_to_openai(claude_request: ClaudeMessagesRequest, model_manager) -> Dict[str, Any]:
    openai_model = model_manager.map_claude_model_to_openai(claude_request.model)

    openai_messages: list[dict[str, Any]] = []
    if claude_request.system:
        system_text = _flatten_system_content(claude_request.system)
        if system_text.strip():
            openai_messages.append({"role": Constants.ROLE_SYSTEM, "content": system_text.strip()})

    i = 0
    while i < len(claude_request.messages):
        msg = claude_request.messages[i]
        if msg.role == Constants.ROLE_USER:
            openai_messages.append(convert_claude_user_message(msg))
        elif msg.role == Constants.ROLE_ASSISTANT:
            openai_messages.append(convert_claude_assistant_message(msg))
            if i + 1 < len(claude_request.messages):
                next_msg = claude_request.messages[i + 1]
                if (
                    next_msg.role == Constants.ROLE_USER
                    and isinstance(next_msg.content, list)
                    and any(getattr(block, "type", None) == Constants.CONTENT_TOOL_RESULT for block in next_msg.content)
                ):
                    i += 1
                    openai_messages.extend(convert_claude_tool_results(next_msg))
        i += 1

    openai_request: Dict[str, Any] = {
        "model": openai_model,
        "messages": openai_messages,
        "max_tokens": min(max(claude_request.max_tokens, proxy_config.min_tokens_limit), proxy_config.max_tokens_limit),
        "temperature": claude_request.temperature,
        "stream": bool(claude_request.stream),
    }

    if claude_request.stop_sequences:
        openai_request["stop"] = claude_request.stop_sequences
    if claude_request.top_p is not None:
        openai_request["top_p"] = claude_request.top_p

    if claude_request.tools:
        openai_tools = []
        for tool in claude_request.tools:
            if tool.name and tool.name.strip():
                openai_tools.append(
                    {
                        "type": Constants.TOOL_FUNCTION,
                        Constants.TOOL_FUNCTION: {
                            "name": tool.name,
                            "description": tool.description or "",
                            "parameters": tool.input_schema,
                        },
                    }
                )
        if openai_tools:
            openai_request["tools"] = openai_tools

    if claude_request.tool_choice:
        choice_type = claude_request.tool_choice.get("type")
        if choice_type in {"auto", "any"}:
            openai_request["tool_choice"] = "auto"
        elif choice_type == Constants.TOOL_FUNCTION:
            openai_request["tool_choice"] = {"type": Constants.TOOL_FUNCTION, "function": claude_request.tool_choice.get("function")}

    logger.debug("Converted Claude request to OpenAI format: %s", json.dumps(openai_request, ensure_ascii=False))
    return openai_request
