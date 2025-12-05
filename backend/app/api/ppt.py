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
    topic: str, stage: str | None = None, service: PPTWorkflowService = Depends(get_service)
) -> PromptNotebookResponse:
    return service.read_notebook(topic, stage)
