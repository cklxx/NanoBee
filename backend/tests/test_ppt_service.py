import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import Settings
import httpx

from app.ppt.prompts import PromptNotebook
from app.ppt.providers import DoubaoTextProvider, SeaDreamImageProvider
from app.ppt.schemas import ImagesRequest, OutlineRequest, SearchRequest, SlidesRequest
from app.ppt.service import MAX_SLIDES, PPTWorkflowService


def test_generate_references_and_outline(tmp_path):
    service = PPTWorkflowService(Settings(workspaces_root=tmp_path))
    search_resp = service.generate_references(SearchRequest(topic="新能源战略", limit=5))

    ranks = [ref.rank for ref in search_resp.references]
    assert ranks == sorted(ranks)
    assert search_resp.references[0].source in {"官方机构", "研究院校"}

    outline_resp = service.generate_outline(
        OutlineRequest(topic="新能源战略", references=search_resp.references)
    )

    assert len(outline_resp.outline) == 5
    slug = PromptNotebook._slugify("新能源战略")
    prompt_path = tmp_path / "ppt" / slug / "search.md"
    assert prompt_path.exists()

    notebook_state = service.read_notebook("新能源战略", stage="outline")
    assert all(record.stage == "outline" for record in notebook_state.prompts)


def test_generate_slides_and_images_follow_style_seed(tmp_path):
    service = PPTWorkflowService(Settings(workspaces_root=tmp_path))
    references = service.generate_references(SearchRequest(topic="AI 产品发布", limit=6)).references
    outline = service.generate_outline(
        OutlineRequest(topic="AI 产品发布", references=references)
    )

    slides_resp = service.generate_slides(
        SlidesRequest(
            topic="AI 产品发布",
            outline=outline.outline,
            style_prompt="商务简洁",
            references=references,
        )
    )

    assert len(slides_resp.slides) <= MAX_SLIDES
    assert slides_resp.slides[-1].title.endswith("参考资料索引")
    assert slides_resp.slides[0].sources

    images_resp = service.generate_images(
        ImagesRequest(topic="AI 产品发布", slides=slides_resp.slides, watermark=None)
    )

    assert len(images_resp.images) == len(slides_resp.slides)
    assert all(img.data_url.startswith("data:image/svg+xml;base64,") for img in images_resp.images)
    assert images_resp.images[0].model == service.settings.default_image_model
    assert images_resp.images[0].watermark is service.settings.allow_image_watermark

    notebook_path = (
        tmp_path
        / "ppt"
        / PromptNotebook._slugify("AI 产品发布")
        / "images.md"
    )
    assert notebook_path.exists()


def test_text_provider_outline_is_used_when_configured(tmp_path):
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": "章节：封面\n- 概要\n章节：执行摘要\n- 关键指标",
                        }
                    }
                ]
            },
        )
    )
    client = httpx.Client(transport=transport)
    text_provider = DoubaoTextProvider(
        model="doubao-seed-1-6-251015",
        base_url="https://mock.volcengine/v3/chat",
        api_key="sk-test",
        client=client,
    )

    service = PPTWorkflowService(Settings(workspaces_root=tmp_path), text_provider=text_provider)

    response = service.generate_outline(
        OutlineRequest(topic="新零售", references=[])
    )

    assert any(section.title == "封面" for section in response.outline)
    assert any(section.title == "执行摘要" for section in response.outline)


def test_image_provider_generates_png_data_url(tmp_path):
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={"data": [{"b64_json": "ZmFrZS1pbWc="}]},
        )
    )
    client = httpx.Client(transport=transport)
    image_provider = SeaDreamImageProvider(
        model="doubao-seedream-4-5-251128",
        base_url="https://mock.volcengine/v1/images",
        api_key="sk-image",
        client=client,
    )

    service = PPTWorkflowService(
        Settings(workspaces_root=tmp_path), image_provider=image_provider
    )
    slides = [
        service._reference_index_slide("测试主题", [])
    ]

    response = service.generate_images(ImagesRequest(slides=slides))

    assert response.images[0].data_url.startswith("data:image/png;base64,ZmFrZS1pbWc=")
