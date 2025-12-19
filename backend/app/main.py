"""FastAPI entrypoint exposing the Claude agent and PPT skills."""
from __future__ import annotations
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .agent import summarize_run
from .config import settings
from .skills import create_ppt_visuals_handler

app = FastAPI(title="NanoBee Agent", version="1.0.0")


class PromptRequest(BaseModel):
    prompt: str = Field(..., description="User prompt for the PPT agent")


class VisualRequest(BaseModel):
    topic: str = Field(..., description="PPT主题")
    narrative: str | None = Field(None, description="视觉叙述或风格")
    slides: int = Field(default=0, description="需要生成的页数，0则使用默认值")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/agent/run")
async def run_agent_endpoint(payload: PromptRequest) -> dict[str, Any]:
    result = await summarize_run(payload.prompt)
    # convert messages to repr to avoid non-serializable types
    serialised = [repr(msg) for msg in result.pop("messages", [])]
    return {"messages": serialised, **result}


@app.post("/skills/visuals")
async def run_visual_skill(payload: VisualRequest) -> dict[str, Any]:
    slides = payload.slides or settings.default_slide_count
    try:
        result = await create_ppt_visuals_handler(
            {"topic": payload.topic, "narrative": payload.narrative or "", "slides": slides}
        )
    except Exception as exc:  # pragma: no cover - defensive for HTTP layer
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return result
