from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    model: str
    base_url: str
    api_key: Optional[str] = Field(default=None, description="Optional API key for the provider")


class ReferenceArticle(BaseModel):
    title: str
    url: str
    summary: str
    source: str = Field(default="search", description="Where the reference was retrieved from")
    rank: int = Field(default=0, description="Authority rank (1 = highest)")


class SearchRequest(BaseModel):
    topic: str = Field(..., description="User provided PPT theme")
    limit: int = Field(default=5, ge=1, le=12, description="How many references to surface")
    source_hint: Optional[str] = Field(default=None, description="Optional hint for retrieval channel")
    session_id: Optional[str] = Field(
        default=None, description="Session identifier to scope prompt history"
    )


class SearchResponse(BaseModel):
    topic: str
    references: List[ReferenceArticle]


class OutlineSection(BaseModel):
    title: str
    bullets: List[str]


class OutlineRequest(BaseModel):
    topic: str
    references: List[ReferenceArticle]
    text_model: Optional[ModelConfig] = None
    session_id: Optional[str] = Field(
        default=None, description="Session identifier to scope prompt history"
    )


class OutlineResponse(BaseModel):
    topic: str
    outline: List[OutlineSection]


class Palette(BaseModel):
    primary: str
    secondary: str
    accent: str


class SlideContent(BaseModel):
    title: str
    bullets: List[str]
    palette: Palette
    keywords: str
    style_prompt: Optional[str] = Field(default=None, description="Free-form style or tone hints")
    sources: List[int] = Field(
        default_factory=list,
        description="1-based reference indices included on this slide",
    )


class SlidesRequest(BaseModel):
    topic: str
    outline: List[OutlineSection]
    style_prompt: Optional[str] = None
    references: Optional[List[ReferenceArticle]] = None
    text_model: Optional[ModelConfig] = None
    session_id: Optional[str] = Field(
        default=None, description="Session identifier to scope prompt history"
    )


class SlidesResponse(BaseModel):
    slides: List[SlideContent]


class SlideImage(BaseModel):
    title: str
    style_seed: str
    model: str
    base_url: str
    watermark: bool
    url: Optional[str] = Field(default=None, description="Publicly accessible image URL or data URL")
    data_url: Optional[str] = Field(
        default=None,
        description="Legacy data URL (base64 or SVG). May be omitted when a public URL is returned.",
    )


class ImagesRequest(BaseModel):
    topic: Optional[str] = Field(
        default=None, description="Topic used to scope the image prompt notebook"
    )
    slides: List[SlideContent]
    image_model: Optional[ModelConfig] = None
    watermark: Optional[bool] = None
    session_id: Optional[str] = Field(
        default=None, description="Session identifier to scope prompt history"
    )


class ImagesResponse(BaseModel):
    images: List[SlideImage]


class PromptRecord(BaseModel):
    stage: str = Field(description="Stage name, e.g., search/outline/slides/images")
    path: str = Field(description="Path of the Markdown notebook on disk")
    content: str = Field(description="Markdown content for the stored prompt")


class PromptNotebookResponse(BaseModel):
    topic: str
    prompts: List[PromptRecord]
