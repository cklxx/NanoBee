from __future__ import annotations

from fastapi import APIRouter, Depends

from ..config import Settings, get_settings
from ..ppt.schemas import (
    ImagesRequest,
    ImagesResponse,
    OutlineRequest,
    OutlineResponse,
    PromptNotebookResponse,
    SearchRequest,
    SearchResponse,
    SlidesRequest,
    SlidesResponse,
)
from ..ppt.service import PPTWorkflowService

router = APIRouter(prefix="/api/ppt", tags=["ppt-workflow"])


def get_service(settings: Settings = Depends(get_settings)) -> PPTWorkflowService:
    return PPTWorkflowService(settings=settings)


@router.post("/search", response_model=SearchResponse)
async def search_references(
    body: SearchRequest, service: PPTWorkflowService = Depends(get_service)
) -> SearchResponse:
    return service.generate_references(body)


@router.post("/outline", response_model=OutlineResponse)
async def build_outline(
    body: OutlineRequest, service: PPTWorkflowService = Depends(get_service)
) -> OutlineResponse:
    return service.generate_outline(body)


@router.post("/outline-stream")
async def build_outline_stream(
    body: OutlineRequest, service: PPTWorkflowService = Depends(get_service)
):
    """
    SSE streaming endpoint for progressive outline generation.
    Yields events after each round completes.
    """
    from fastapi.responses import StreamingResponse
    import json
    
    def generate():
        try:
            for event in service.generate_outline_stream(body):
                # Format as SSE event
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            error_event = {"type": "error", "error": str(e)}
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering
        }
    )



@router.post("/slides", response_model=SlidesResponse)
async def build_slides(
    body: SlidesRequest, service: PPTWorkflowService = Depends(get_service)
) -> SlidesResponse:
    return service.generate_slides(body)


@router.post("/images", response_model=ImagesResponse)
async def build_images(
    body: ImagesRequest, service: PPTWorkflowService = Depends(get_service)
) -> ImagesResponse:
    return service.generate_images(body)


@router.get("/prompts", response_model=PromptNotebookResponse)
async def read_prompts(
    topic: str,
    stage: str | None = None,
    session_id: str | None = None,
    service: PPTWorkflowService = Depends(get_service),
) -> PromptNotebookResponse:
    return service.read_notebook(topic, stage, session_id)
