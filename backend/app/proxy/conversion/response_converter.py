"""Convert OpenAI chat completion responses into Anthropic-compatible shapes."""
from __future__ import annotations

import json
import uuid
from typing import AsyncGenerator

from fastapi import HTTPException

from ..constants import Constants
from ..models.claude import ClaudeMessagesRequest


def convert_openai_to_claude_response(openai_response: dict, original_request: ClaudeMessagesRequest) -> dict:
    choices = openai_response.get("choices", [])
    if not choices:
        raise HTTPException(status_code=500, detail="No choices in OpenAI response")

    choice = choices[0]
    message = choice.get("message", {})

    content_blocks: list[dict[str, object]] = []
    text_content = message.get("content")
    if text_content is not None:
        content_blocks.append({"type": Constants.CONTENT_TEXT, "text": text_content})

    tool_calls = message.get("tool_calls", []) or []
    for tool_call in tool_calls:
        if tool_call.get("type") == Constants.TOOL_FUNCTION:
            function_data = tool_call.get(Constants.TOOL_FUNCTION, {})
            try:
                arguments = json.loads(function_data.get("arguments", "{}"))
            except json.JSONDecodeError:
                arguments = {"raw_arguments": function_data.get("arguments", "")}
            content_blocks.append(
                {
                    "type": Constants.CONTENT_TOOL_USE,
                    "id": tool_call.get("id", f"tool_{uuid.uuid4()}"),
                    "name": function_data.get("name", ""),
                    "input": arguments,
                }
            )

    if not content_blocks:
        content_blocks.append({"type": Constants.CONTENT_TEXT, "text": ""})

    finish_reason = choice.get("finish_reason", "stop")
    stop_reason = {
        "stop": Constants.STOP_END_TURN,
        "length": Constants.STOP_MAX_TOKENS,
        "tool_calls": Constants.STOP_TOOL_USE,
        "function_call": Constants.STOP_TOOL_USE,
    }.get(finish_reason, Constants.STOP_END_TURN)

    return {
        "id": openai_response.get("id", f"msg_{uuid.uuid4()}"),
        "type": "message",
        "role": Constants.ROLE_ASSISTANT,
        "model": original_request.model,
        "content": content_blocks,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {
            "input_tokens": openai_response.get("usage", {}).get("prompt_tokens", 0),
            "output_tokens": openai_response.get("usage", {}).get("completion_tokens", 0),
        },
    }


async def convert_openai_streaming_to_claude(
    openai_stream: AsyncGenerator[str, None], original_request: ClaudeMessagesRequest, logger
):
    message_id = f"msg_{uuid.uuid4().hex[:24]}"

    yield (
        f"event: {Constants.EVENT_MESSAGE_START}\n"
        f"data: {json.dumps({'type': Constants.EVENT_MESSAGE_START, 'message': {'id': message_id, 'type': 'message', 'role': Constants.ROLE_ASSISTANT, 'model': original_request.model, 'content': [], 'stop_reason': None, 'stop_sequence': None, 'usage': {'input_tokens': 0, 'output_tokens': 0}}}, ensure_ascii=False)}\n\n"
    )
    yield (
        f"event: {Constants.EVENT_CONTENT_BLOCK_START}\n"
        f"data: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_START, 'index': 0, 'content_block': {'type': Constants.CONTENT_TEXT, 'text': ''}}, ensure_ascii=False)}\n\n"
    )
    yield f"event: {Constants.EVENT_PING}\ndata: {json.dumps({'type': Constants.EVENT_PING}, ensure_ascii=False)}\n\n"

    text_block_index = 0
    tool_block_counter = 0
    current_tool_calls: dict[int, dict[str, object]] = {}
    final_stop_reason = Constants.STOP_END_TURN

    try:
        async for line in openai_stream:
            if not line.strip():
                continue
            if not line.startswith("data: "):
                continue
            chunk_data = line[6:]
            if chunk_data.strip() == "[DONE]":
                break
            try:
                chunk = json.loads(chunk_data)
                choices = chunk.get("choices", [])
                if not choices:
                    continue
            except json.JSONDecodeError as exc:  # pragma: no cover - defensive
                logger.warning("Failed to parse chunk: %s error=%s", chunk_data, exc)
                continue

            choice = choices[0]
            delta = choice.get("delta", {})
            finish_reason = choice.get("finish_reason")

            if delta and "content" in delta and delta["content"] is not None:
                yield (
                    f"event: {Constants.EVENT_CONTENT_BLOCK_DELTA}\n"
                    f"data: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_DELTA, 'index': text_block_index, 'delta': {'type': Constants.DELTA_TEXT, 'text': delta['content']}}, ensure_ascii=False)}\n\n"
                )

            if "tool_calls" in delta:
                for tc_delta in delta["tool_calls"]:
                    tc_index = tc_delta.get("index", 0)
                    if tc_index not in current_tool_calls:
                        current_tool_calls[tc_index] = {
                            "id": None,
                            "name": None,
                            "args_buffer": "",
                            "json_sent": False,
                            "claude_index": None,
                            "started": False,
                        }

                    tool_call = current_tool_calls[tc_index]
                    if tc_delta.get("id"):
                        tool_call["id"] = tc_delta["id"]

                    function_data = tc_delta.get(Constants.TOOL_FUNCTION, {})
                    if function_data.get("name"):
                        tool_call["name"] = function_data["name"]

                    if tool_call["id"] and tool_call["name"] and not tool_call["started"]:
                        tool_block_counter += 1
                        claude_index = text_block_index + tool_block_counter
                        tool_call["claude_index"] = claude_index
                        tool_call["started"] = True
                        yield (
                            f"event: {Constants.EVENT_CONTENT_BLOCK_START}\n"
                            f"data: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_START, 'index': claude_index, 'content_block': {'type': Constants.CONTENT_TOOL_USE, 'id': tool_call['id'], 'name': tool_call['name'], 'input': {}}}, ensure_ascii=False)}\n\n"
                        )

                    if "arguments" in function_data and tool_call["started"] and function_data["arguments"] is not None:
                        tool_call["args_buffer"] += function_data["arguments"]
                        try:
                            json.loads(tool_call["args_buffer"])
                            if not tool_call["json_sent"]:
                                yield (
                                    f"event: {Constants.EVENT_CONTENT_BLOCK_DELTA}\n"
                                    f"data: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_DELTA, 'index': tool_call['claude_index'], 'delta': {'type': Constants.DELTA_INPUT_JSON, 'partial_json': tool_call['args_buffer']}}, ensure_ascii=False)}\n\n"
                                )
                                tool_call["json_sent"] = True
                        except json.JSONDecodeError:
                            pass

            if finish_reason:
                if finish_reason == "length":
                    final_stop_reason = Constants.STOP_MAX_TOKENS
                elif finish_reason in ["tool_calls", "function_call"]:
                    final_stop_reason = Constants.STOP_TOOL_USE
                elif finish_reason == "stop":
                    final_stop_reason = Constants.STOP_END_TURN
                else:
                    final_stop_reason = Constants.STOP_END_TURN
                break
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Streaming error: %s", exc)
        error_event = {"type": "error", "error": {"type": "api_error", "message": f"Streaming error: {exc}"}}
        yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
        return

    yield (
        f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\n"
        f"data: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_STOP, 'index': text_block_index}, ensure_ascii=False)}\n\n"
    )

    for tool_call in current_tool_calls.values():
        if tool_call.get("started"):
            yield (
                f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\n"
                f"data: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_STOP, 'index': tool_call['claude_index']}, ensure_ascii=False)}\n\n"
            )

    yield (
        f"event: {Constants.EVENT_MESSAGE_STOP}\n"
        f"data: {json.dumps({'type': Constants.EVENT_MESSAGE_STOP, 'message': {'id': message_id, 'type': 'message', 'role': Constants.ROLE_ASSISTANT, 'model': original_request.model, 'content': [], 'stop_reason': final_stop_reason, 'stop_sequence': None, 'usage': {'input_tokens': 0, 'output_tokens': 0}}}, ensure_ascii=False)}\n\n"
    )
