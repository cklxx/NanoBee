"""Skill implementations exposed to the Claude agent."""
from __future__ import annotations

from datetime import datetime
from textwrap import dedent

from claude_agent_sdk import tool

from .config import settings
from .image_client import ImageGenerationClient, build_slide_prompts

image_client = ImageGenerationClient()


@tool(
    name="draft_ppt_outline",
    description="生成PPT的大纲和分镜，帮助明确每页的叙述重点",
    input_schema={"topic": str, "audience": str, "slides": int},
)
async def draft_ppt_outline(args: dict) -> dict:
    topic: str = args.get("topic", "未知主题")
    audience: str = args.get("audience", "通用观众")
    slides: int = int(args.get("slides") or settings.default_slide_count)

    outline_lines = [
        f"主题：{topic}",
        f"受众：{audience}",
        f"预计页数：{slides}页",
        "\n章节规划：",
    ]
    outline_lines.extend(
        [f"- 第{idx + 1}页：聚焦核心要点，包含标题、3个要点和辅助视觉。" for idx in range(slides)]
    )

    return {"content": [{"type": "text", "text": "\n".join(outline_lines)}]}


@tool(
    name="create_ppt_visuals",
    description="调用生图LLM，为每页PPT生成可视化效果草图",
    input_schema={"topic": str, "slides": int, "narrative": str},
)
async def create_ppt_visuals(args: dict) -> dict:
    topic: str = args.get("topic", "未指定主题")
    narrative: str | None = args.get("narrative") or None
    slides: int = max(1, int(args.get("slides") or settings.default_slide_count))

    prompts = build_slide_prompts(topic, narrative, slides)
    images = await image_client.generate_images(prompts)

    content_blocks = [
        {
            "type": "text",
            "text": dedent(
                f"""
                生图任务完成：
                - 主题: {topic}
                - 叙述: {narrative or '使用默认叙述'}
                - 页数: {slides}
                - 时间: {datetime.utcnow().isoformat()}Z
                """
            ).strip(),
        }
    ]

    for item in images:
        caption = item.get("prompt", "")
        url = item.get("url") or "未提供URL，请查看raw字段"
        content_blocks.append({"type": "text", "text": f"{caption}\n图像: {url}"})

    return {"content": content_blocks, "raw": images}
