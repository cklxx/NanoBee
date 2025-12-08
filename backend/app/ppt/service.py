from __future__ import annotations

import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from ..config import Settings
from .providers import DoubaoTextProvider, ImageResult, SeaDreamImageProvider
from .prompts import PromptNotebook
from .schemas import (
    ImagesRequest,
    ImagesResponse,
    ModelConfig,
    OutlineRequest,
    OutlineResponse,
    OutlineSection,
    Palette,
    PromptNotebookResponse,
    PromptRecord,
    ReferenceArticle,
    SearchRequest,
    SearchResponse,
    SlideContent,
    SlideImage,
    SlidesRequest,
    SlidesResponse,
)

MAX_SLIDES = 15
DEFAULT_PALETTE = Palette(primary="#0f172a", secondary="#6366f1", accent="#f59e0b")
PROMPTS_DIR = Path(__file__).parent / "prompts"



@dataclass
class PPTWorkflowService:
    settings: Settings
    text_provider: DoubaoTextProvider | None = None
    image_provider: SeaDreamImageProvider | None = None
    notebook_root: Path = field(init=False)

    def __post_init__(self) -> None:
        self.notebook_root = Path(self.settings.workspaces_root)
        self.notebook_root.mkdir(parents=True, exist_ok=True)
        if not self.text_provider:
            self.text_provider = DoubaoTextProvider(
                model=self.settings.default_text_model,
                base_url=self._normalize_url(self.settings.default_text_base_url, "default_text_base_url"),
                api_key=self.settings.text_api_key,
            )
        if not self.image_provider:
            self.image_provider = SeaDreamImageProvider(
                model=self.settings.default_image_model,
                base_url=self._normalize_url(self.settings.default_image_base_url, "default_image_base_url"),
                api_key=self.settings.image_api_key,
            )

    def read_notebook(self, topic: str, stage: str | None = None, session_id: str | None = None) -> PromptNotebookResponse:
        notebook = self._notebook(topic, session_id)
        stages = [stage] if stage else ["search", "outline", "slides", "images"]

        prompts: list[PromptRecord] = []
        for name in stages:
            content = notebook.read_prompt(name)
            if content is None:
                continue
            prompts.append(
                PromptRecord(
                    stage=name,
                    path=str(notebook.prompt_path(name)),
                    content=content,
                )
            )

        return PromptNotebookResponse(topic=topic, prompts=prompts)

    def generate_references(self, request: SearchRequest) -> SearchResponse:
        """使用真实Web搜索生成参考资料"""
        notebook = self._notebook(request.topic, request.session_id)
        notebook.save_prompt(
            "search",
            self._build_search_prompt(request),
        )

        references: list[ReferenceArticle] = []
        
        try:
            # 使用 DuckDuckGo 进行真实Web搜索
            from ddgs import DDGS
            
            with DDGS() as ddgs:
                # 搜索相关结果
                results = list(
                    ddgs.text(
                        query=f"{request.topic} 研究 分析 报告",
                        max_results=request.limit,
                        region="cn-zh",  # 中文地区
                    )
                )
                
                for result in results:
                    # 智能判断来源类型
                    url = result.get('href', '')
                    source_type = self._determine_source_type(url)
                    
                    references.append(
                        ReferenceArticle(
                            title=result.get('title', ''),
                            source=source_type,
                            url=url,
                            summary=result.get('body', '')[:100] + '...' if len(result.get('body', '')) > 100 else result.get('body', ''),
                        )
                    )
        except Exception as e:
            print(f"Web search failed: {e}")
            # 降级：使用基于规则的参考建议
            references = self._generate_fallback_references(request)

        if not references:
            # 最终降级：返回基于规则的参考
            references = self._generate_fallback_references(request)

        # 按权威性排序
        ranked = self._rank_references(references)
        return SearchResponse(topic=request.topic, references=ranked)

    def _determine_source_type(self, url: str) -> str:
        """根据URL判断来源类型"""
        if 'gov.cn' in url or '.gov' in url:
            return '政府机构'
        elif 'edu.cn' in url or '.edu' in url:
            return '教育机构'
        elif 'scholar.google' in url or 'researchgate' in url or 'arxiv' in url:
            return '学术论文'
        elif 'github.com' in url or 'gitlab.com' in url:
            return '开源社区'
        elif 'zhihu.com' in url:
            return '知识社区'
        elif 'baidu.com' in url:
            return '综合搜索'
        else:
            return '行业资讯'

    def _generate_fallback_references(self, request: SearchRequest) -> list[ReferenceArticle]:
        """降级方案：使用LLM生成真实参考知识"""
        references: list[ReferenceArticle] = []
        
        # 尝试使用LLM生成有价值的参考知识
        if self.text_provider and self.text_provider.can_call:
            try:
                template = self._load_prompt_template("search_references.md")
                if template:
                    prompt = template.format(topic=request.topic, limit=request.limit)
                else:
                    prompt = (
                        f"作为专家，为主题'{request.topic}'推荐{request.limit}个最权威的信息来源方向。"
                        f"对每个方向，说明：1)应该查找什么类型的资料 2)这类资料能提供什么价值。"
                        f"格式：每行一个，用 | 分隔：资料方向|资料类型|价值说明"
                    )

                content = self.text_provider.generate(prompt)
                
                for line in content.splitlines():
                    line = line.strip()
                    if not line or "|" not in line:
                        continue
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 3:
                        direction, source_type, value = parts[0], parts[1], parts[2]
                        # 生成建议性搜索链接
                        search_query = f"{request.topic} {direction}".replace(" ", "+")
                        url = f"https://www.google.com/search?q={search_query}"
                        
                        references.append(
                            ReferenceArticle(
                                title=direction,
                                source=source_type,
                                url=url,
                                summary=value,
                            )
                        )
                
                if len(references) >= request.limit:
                    return references[:request.limit]
                    
            except Exception as e:
                print(f"LLM fallback generation failed: {e}")
        
        # 如果LLM也失败，返回空列表（而不是假数据）
        return []

    def generate_outline(self, request: OutlineRequest) -> OutlineResponse:
        notebook = self._notebook(request.topic, request.session_id)
        outline_prompt = self._build_outline_prompt(request)
        notebook.save_prompt("outline", outline_prompt)

        top_refs = request.references[:3]
        context = "、".join(ref.title for ref in top_refs) or "用户输入"
        
        # Use multi-round generation for better reliability
        outline = self._generate_outline_in_rounds(request, context, outline_prompt)
        if not outline:
            raise RuntimeError("Outline generation failed: no content returned from model")

        return OutlineResponse(topic=request.topic, outline=outline)
    
    def generate_outline_stream(self, request: OutlineRequest):
        """
        生成器函数，yield SSE events for progressive outline generation.
        Yields dict objects that will be JSON-serialized by the endpoint.
        """
        notebook = self._notebook(request.topic, request.session_id)
        outline_prompt = self._build_outline_prompt(request)
        notebook.save_prompt("outline", outline_prompt)
        
        context = "、".join(ref.title for ref in request.references[:3]) or "用户输入"
        base_prompt = outline_prompt
        all_sections: list[OutlineSection] = []
        
        try:
            # Round 1: 第1-5页
            yield {"type": "progress", "round": 1, "total_rounds": 3, "message": "正在生成第1-5页..."}
            print("[Outline Stream] Starting Round 1/3: Pages 1-5")
            
            round1_prompt = f"""{base_prompt}

## 当前任务
请生成第 1-5 页，包括：
1. 封面：主题 + 核心价值
2. 背景：行业现状/宏观环境
3. 挑战：核心问题/痛点
4-5. 解决方案（开篇）：关键方法论的前2个要点

请确保这5页构成完整的开篇部分（背景→问题→初步方案）。
"""
            
            sections_round1 = self._generate_outline_from_model(request, context, round1_prompt)
            if not sections_round1:
                yield {"type": "error", "error": "Round 1 failed: no content returned"}
                return
            
            all_sections.extend(sections_round1)
            print(f"[Outline Stream] ✓ Round 1 complete: {len(sections_round1)} sections")
            yield {
                "type": "partial",
                "round": 1,
                "sections": [s.model_dump() for s in sections_round1],
                "total": len(all_sections),
                "message": f"第1轮完成，已生成{len(all_sections)}页"
            }
            
            # Round 2: 第6-10页
            yield {"type": "progress", "round": 2, "total_rounds": 3, "message": "正在生成第6-10页..."}
            print("[Outline Stream] Starting Round 2/3: Pages 6-10")
            
            previous_context = self._format_sections_as_context(all_sections)
            round2_prompt = f"""{base_prompt}

## 已生成内容（第1-5页）
{previous_context}

## 当前任务
请继续生成第 6-10 页，包括：
6-7. 解决方案（深入）：核心方法论的展开说明
8-9. 论证/案例：数据支撑、案例分析
10. 对比优势：与traditional方法对比

请确保与前5页逻辑连贯，深入展开解决方案。
"""
            
            sections_round2 = self._generate_outline_from_model(request, context, round2_prompt)
            if not sections_round2:
                print("[Outline Stream] Round 2 failed, returning partial results")
                yield {
                    "type": "partial_complete",
                    "outline": [s.model_dump() for s in all_sections],
                    "total": len(all_sections),
                    "message": f"第2轮失败，已生成{len(all_sections)}页"
                }
                return
            
            all_sections.extend(sections_round2)
            print(f"[Outline Stream] ✓ Round 2 complete: {len(sections_round2)} sections (total: {len(all_sections)})")
            yield {
                "type": "partial",
                "round": 2,
                "sections": [s.model_dump() for s in sections_round2],
                "total": len(all_sections),
                "message": f"第2轮完成，已生成{len(all_sections)}页"
            }
            
            # Round 3: 第11-15页
            yield {"type": "progress", "round": 3, "total_rounds": 3, "message": "正在生成第11-15页..."}
            print("[Outline Stream] Starting Round 3/3: Pages 11-15")
            
            previous_context = self._format_sections_as_context(all_sections)
            round3_prompt = f"""{base_prompt}

## 已生成内容（第1-10页）
{previous_context}

## 当前任务
请继续生成第 11-15 页（结尾部分），包括：
11-12. 展望：未来趋势、发展方向
13-14. 行动建议：具体实施步骤
15. 封底：总结金句

请确保这5页构成完整的收尾，呼应开篇主题。
"""
            
            sections_round3 = self._generate_outline_from_model(request, context, round3_prompt)
            if not sections_round3:
                print("[Outline Stream] Round 3 failed, returning partial results")
                yield {
                    "type": "partial_complete",
                    "outline": [s.model_dump() for s in all_sections],
                    "total": len(all_sections),
                    "message": f"第3轮失败，已生成{len(all_sections)}页"
                }
                return
            
            all_sections.extend(sections_round3)
            print(f"[Outline Stream] ✓ Round 3 complete: {len(sections_round3)} sections")
            print(f"[Outline Stream] 🎉 All rounds complete! Total: {len(all_sections)} sections")
            
            # Final complete event
            yield {
                "type": "complete",
                "outline": [s.model_dump() for s in all_sections],
                "total": len(all_sections),
                "message": f"大纲生成完成，共{len(all_sections)}个部分"
            }
            
        except Exception as e:
            print(f"[Outline Stream] Error: {e}")
            import traceback
            traceback.print_exc()
            yield {"type": "error", "error": str(e)}

    
    def _generate_outline_in_rounds(
        self, request: OutlineRequest, context: str, base_prompt: str
    ) -> list[OutlineSection] | None:
        """
        生成大纲，分3轮进行：
        - Round 1: 页 1-5 (封面、背景、挑战、解决方案1-2)
        - Round 2: 页 6-10 (解决方案3-4、论证、案例)
        - Round 3: 页 11-15 (对比、展望、行动建议、封底)
        """
        all_sections: list[OutlineSection] = []
        
        # Round 1: 第1-5页
        print("[Outline] Starting Round 1/3: Pages 1-5")
        round1_prompt = f"""{base_prompt}

## 当前任务
请生成第 1-5 页，包括：
1. 封面：主题 + 核心价值
2. 背景：行业现状/宏观环境
3. 挑战：核心问题/痛点
4-5. 解决方案（开篇）：关键方法论的前2个要点

请确保这5页构成完整的开篇部分（背景→问题→初步方案）。
"""
        
        sections_round1 = self._generate_outline_from_model(request, context, round1_prompt)
        if not sections_round1:
            print("[Outline] Round 1 failed, aborting")
            return None
        
        all_sections.extend(sections_round1)
        print(f"[Outline] ✓ Round 1 complete: {len(sections_round1)} sections")
        
        # Round 2: 第6-10页，基于Round 1
        print("[Outline] Starting Round 2/3: Pages 6-10")
        previous_context = self._format_sections_as_context(all_sections)
        round2_prompt = f"""{base_prompt}

## 已生成内容（第1-5页）
{previous_context}

## 当前任务
请继续生成第 6-10 页，包括：
6-7. 解决方案（深入）：核心方法论的展开说明
8-9. 论证/案例：数据支撑、案例分析
10. 对比优势：与tradicional方法对比

请确保与前5页逻辑连贯，深入展开解决方案。
"""
        
        sections_round2 = self._generate_outline_from_model(request, context, round2_prompt)
        if not sections_round2:
            print("[Outline] Round 2 failed, returning partial results from Round 1")
            return all_sections  # 返回部分结果
        
        all_sections.extend(sections_round2)
        print(f"[Outline] ✓ Round 2 complete: {len(sections_round2)} sections (total: {len(all_sections)})")
        
        # Round 3: 第11-15页
        print("[Outline] Starting Round 3/3: Pages 11-15")
        previous_context = self._format_sections_as_context(all_sections)
        round3_prompt = f"""{base_prompt}

## 已生成内容（第1-10页）
{previous_context}

## 当前任务
请继续生成第 11-15 页（结尾部分），包括：
11-12. 展望：未来趋势、发展方向
13-14. 行动建议：具体实施步骤
15. 封底：总结金句

请确保这5页构成完整的收尾，呼应开篇主题。
"""
        
        sections_round3 = self._generate_outline_from_model(request, context, round3_prompt)
        if not sections_round3:
            print("[Outline] Round 3 failed, returning partial results from Round 1-2")
            return all_sections  # 返回部分结果
        
        all_sections.extend(sections_round3)
        print(f"[Outline] ✓ Round 3 complete: {len(sections_round3)} sections")
        print(f"[Outline] 🎉 All rounds complete! Total: {len(all_sections)} sections")
        
        return all_sections
    
    def _format_sections_as_context(self, sections: list[OutlineSection]) -> str:
        """将已生成的sections格式化为context string"""
        lines = []
        for idx, section in enumerate(sections, 1):
            lines.append(f"{idx}. {section.title}")
            for bullet in section.bullets:
                lines.append(f"   - {bullet}")
        return "\n".join(lines)

    def _outline_section(self, title: str, bullets: list[str]) -> OutlineSection:
        return OutlineSection(title=title, bullets=bullets)

    def generate_slides(self, request: SlidesRequest) -> SlidesResponse:
        notebook = self._notebook(request.topic, request.session_id)
        references = request.references or []
        notebook.save_prompt(
            "slides",
            self._build_slide_prompt(request, references),
        )

        outline_sections = request.outline
        max_content_slots = MAX_SLIDES - 1 if references else MAX_SLIDES
        content_sections = outline_sections[:max_content_slots]

        slides: list[SlideContent] = []
        for idx, section in enumerate(content_sections):
            palette = self._palette_for_slide(idx)
            bullets = self._generate_slide_bullets(request, section)
            slides.append(
                SlideContent(
                    title=section.title,
                    bullets=bullets,
                    palette=palette,
                    keywords=f"{request.topic} · 第{idx + 1}页",
                    style_prompt=request.style_prompt,
                    sources=self._sources_for_slide(idx, references),
                )
            )

        if references:
            slides.append(self._reference_index_slide(request.topic, references))

        return SlidesResponse(slides=slides)

    def generate_images(self, request: ImagesRequest) -> ImagesResponse:
        model = (
            request.image_model.model
            if request.image_model
            else self.settings.default_image_model
        )
        base_url = self._normalize_url(
            request.image_model.base_url if request.image_model else self.settings.default_image_base_url,
            "default_image_base_url",
        )
        api_key = (
            request.image_model.api_key
            if request.image_model and request.image_model.api_key
            else self.settings.image_api_key
        )
        watermark = (
            request.watermark
            if request.watermark is not None
            else self.settings.allow_image_watermark
        )

        base_palette = request.slides[0].palette if request.slides else DEFAULT_PALETTE
        images: list[SlideImage] = []

        def palette_for(idx: int, slide: SlideContent) -> Palette:
            if idx == 0:
                return slide.palette
            return Palette(
                primary=base_palette.primary,
                secondary=base_palette.secondary,
                accent=slide.palette.accent,
            )

        # First slide sequential to anchor shared palette.
        if request.slides:
            first_slide = request.slides[0]
            first_palette = palette_for(0, first_slide)
            image_result = self._build_image_result(first_slide, first_palette, watermark, model, base_url, api_key)
            images.append(
                SlideImage(
                    title=first_slide.title,
                    style_seed=first_slide.keywords,
                    url=image_result.url,
                    data_url=image_result.data_url,
                    model=model,
                    base_url=base_url,
                    watermark=watermark,
                )
            )

        def build_image(idx: int, slide: SlideContent) -> tuple[int, SlideImage]:
            pal = palette_for(idx, slide)
            image_result = self._build_image_result(slide, pal, watermark, model, base_url, api_key)
            return idx, SlideImage(
                title=slide.title,
                style_seed=slide.keywords,
                url=image_result.url,
                data_url=image_result.data_url,
                model=model,
                base_url=base_url,
                watermark=watermark,
            )

        remaining = list(enumerate(request.slides[1:], start=1))
        if remaining:
            max_workers = min(8, len(remaining))
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_map = {executor.submit(build_image, idx, slide): idx for idx, slide in remaining}
                results: dict[int, SlideImage] = {}
                for future in as_completed(future_map):
                    idx, slide_image = future.result()
                    results[idx] = slide_image
                for idx in sorted(results):
                    images.append(results[idx])

        topic = request.topic or (request.slides[0].title if request.slides else "images")
        notebook = self._notebook(topic, request.session_id)
        notebook.save_prompt(
            "images",
            self._build_image_prompt(model, base_url, watermark, len(request.slides)),
        )
        return ImagesResponse(images=images)

    def _notebook(self, topic: str, session_id: str | None = None) -> PromptNotebook:
        return PromptNotebook(root=self.notebook_root, topic=topic, session_id=session_id)

    def _build_image_result(
        self,
        slide: SlideContent,
        palette: Palette,
        watermark: bool,
        model: str,
        base_url: str,
        api_key: str | None,
    ) -> ImageResult:
        if self.image_provider and (api_key or self.image_provider.api_key):
            prompt = self._build_image_caption(slide, palette)
            provider = SeaDreamImageProvider(
                model=model,
                base_url=base_url,
                api_key=api_key or self.image_provider.api_key,
                client=self.image_provider.client,
            )
            print(f"[SeaDream] Attempting to generate image for: {slide.title}")
            print(f"[SeaDream] Prompt: {prompt}")
            print(f"[SeaDream] Model: {model}, Base URL: {base_url}")
            print(f"[SeaDream] API key configured: {bool(api_key or self.image_provider.api_key)}")
            print(f"[SeaDream] Provider can_call: {provider.can_call}")
            
            if provider.can_call:
                try:
                    result = provider.generate(prompt, watermark)
                    print(f"[SeaDream] Successfully generated image for: {slide.title}")
                    return result
                except Exception as e:
                    print(f"[SeaDream] Failed to generate image: {type(e).__name__}: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                if not provider.api_key:
                    print("[SeaDream] Provider cannot call - missing API key")
                elif not provider._valid_url(base_url):
                    print("[SeaDream] Provider cannot call - image base URL missing or invalid. Set NANOBEE_DEFAULT_IMAGE_BASE_URL.")
                else:
                    print("[SeaDream] Provider cannot call - check configuration")
        else:
            print(f"[SeaDream] Image provider not configured or no API key")
        
        print(f"[SeaDream] Falling back to content-based SVG for: {slide.title}")
        data_url = self._build_content_svg(slide, palette)
        return ImageResult(url=data_url, data_url=data_url)

    def _build_content_svg(self, slide: SlideContent, palette: Palette) -> str:
        """生成基于内容的SVG，显示实际的幻灯片内容"""
        # 构建要点列表的SVG
        bullets_svg = ""
        y_offset = 200
        for i, bullet in enumerate(slide.bullets[:5]):  # 最多显示5个要点
            # 截断过长的文本
            text = bullet[:80] + "..." if len(bullet) > 80 else bullet
            bullets_svg += f"""
  <circle cx='80' cy='{y_offset + i * 50}' r='4' fill='white' opacity='0.9'/>
  <text x='100' y='{y_offset + i * 50 + 5}' fill='white' font-family='Arial, sans-serif' font-size='18' opacity='0.95'>{self._escape_xml(text)}</text>"""
        
        # 构建完整的SVG
        svg = f"""
<svg xmlns='http://www.w3.org/2000/svg' width='960' height='540'>
  <defs>
    <linearGradient id='grad' x1='0%' y1='0%' x2='100%' y2='100%'>
      <stop offset='0%' style='stop-color:{palette.primary};stop-opacity:1' />
      <stop offset='100%' style='stop-color:{palette.secondary};stop-opacity:1' />
    </linearGradient>
  </defs>
  <rect width='960' height='540' fill='url(#grad)' />
  <text x='60' y='100' fill='white' font-family='Arial, sans-serif' font-size='42' font-weight='bold'>{self._escape_xml(slide.title)}</text>
  {bullets_svg}
  <text x='60' y='510' fill='white' font-family='Arial, sans-serif' font-size='14' opacity='0.6'>{self._escape_xml(slide.keywords)}</text>
</svg>
"""
        import base64
        encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
        return f"data:image/svg+xml;base64,{encoded}"

    @staticmethod
    def _escape_xml(text: str) -> str:
        """转义XML特殊字符"""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\"", "&quot;")
                .replace("'", "&apos;"))

    def _normalize_url(self, url: str | None, field_name: str) -> str:
        """Ensure URLs are non-empty, falling back to the model default if env provided an empty string."""
        value = (url or "").strip()
        if value:
            return value

        default_field = Settings.model_fields.get(field_name)
        if default_field and default_field.default:
            return str(default_field.default)
        return ""

    def _build_image_caption(self, slide: SlideContent, palette: Palette) -> str:
        accent = f"强调色 {palette.accent}" if palette.accent else ""
        return "".join(
            [
                f"{slide.title}，风格：{slide.style_prompt or '商业简约'}，",
                f"基调：{palette.primary}/{palette.secondary}，{accent}，",
                f"关键词：{slide.keywords}",
            ]
        )

    def _generate_outline_from_model(
        self, request: OutlineRequest, context: str, prompt: str
    ) -> list[OutlineSection] | None:
        content = self._maybe_generate_text(prompt, request.text_model)
        if not content:
            print("[Outline] ERROR: No content returned from text generation")
            return None
        
        # Log the raw content for debugging
        content_preview = content[:500].replace("\n", " ")
        print(f"[Outline] Raw content preview (first 500 chars): {content_preview}")
        print(f"[Outline] Total content length: {len(content)} characters")
        
        # Try JSON format first (as requested by the prompt template)
        import json
        import re
        
        try:
            # Clean up content to extract JSON
            # Look for JSON object or array in the response
            json_match = re.search(r'\{[\s\S]*\}|\[[\s\S]*\]', content)
            if json_match:
                json_str = json_match.group(0)
                json_preview = json_str[:200].replace("\n", " ")
                print(f"[Outline] Found JSON match, preview: {json_preview}...")
                print(f"[Outline] JSON string length: {len(json_str)} characters")
                
                try:
                    data = json.loads(json_str)
                    print(f"[Outline] Successfully parsed JSON, type: {type(data)}")
                   
                    if isinstance(data, dict):
                        print(f"[Outline] JSON keys: {list(data.keys())}")
                except json.JSONDecodeError as json_err:
                    print(f"[Outline] JSON decode error: {json_err}")
                    print(f"[Outline] JSON string that failed to parse: {json_str[:1000]}")
                    raise
                
                # Handle different JSON response formats
                sections: list[OutlineSection] = []
                
                # Format 1: {"ppt_outline": [...]}
                if isinstance(data, dict) and "ppt_outline" in data:
                    outline_data = data["ppt_outline"]
                    print(f"[Outline] Using 'ppt_outline' key, found {len(outline_data)} items")
                elif isinstance(data, dict) and "outline" in data:
                    outline_data = data["outline"]
                    print(f"[Outline] Using 'outline' key, found {len(outline_data)} items")
                elif isinstance(data, list):
                    outline_data = data
                    print(f"[Outline] Using direct array, found {len(outline_data)} items")
                else:
                    # Unknown format, fall through to text parsing
                    print(f"[Outline] Unknown JSON format, data type: {type(data)}, keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
                    raise ValueError("Unknown JSON format")
                
                for idx, item in enumerate(outline_data):
                    if isinstance(item, dict):
                        title = item.get("title", "")
                        bullets = item.get("bullets", [])
                        print(f"[Outline] Item {idx}: title='{title[:50]}...', bullets_count={len(bullets)}")
                        if title and bullets:
                            sections.append(self._outline_section(title, bullets))
                        else:
                            print(f"[Outline] WARNING: Item {idx} missing title or bullets")
                    else:
                        print(f"[Outline] WARNING: Item {idx} is not a dict, type: {type(item)}")
                
                if sections:
                    print(f"[Outline] ✓ Successfully parsed {len(sections)} sections from JSON format")
                    return sections
                else:
                    print("[Outline] WARNING: JSON parsed but no valid sections found")
            else:
                print("[Outline] No JSON pattern found in content")
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            # JSON parsing failed, fall back to text format
            print(f"[Outline] JSON parsing failed: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
        
        # Fallback: Parse text format ("章节:" style)
        print("[Outline] Attempting text format parsing...")
        sections: list[OutlineSection] = []
        current_title: str | None = None
        bullets: list[str] = []
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("章节") or stripped.endswith("章节"):
                if current_title and bullets:
                    sections.append(self._outline_section(current_title, bullets))
                if "：" in stripped:
                    current_title = stripped.split("：", 1)[-1].strip()
                else:
                    current_title = stripped.split(":", 1)[-1].strip()
                current_title = current_title or stripped.lstrip("章节：:")
                bullets = []
                continue
            if stripped.startswith("-"):
                bullets.append(stripped.lstrip("- "))
        if current_title and bullets:
            sections.append(self._outline_section(current_title, bullets))
        
        if sections:
            print(f"[Outline] ✓ Parsed {len(sections)} sections from text format")
        else:
            print("[Outline] ERROR: No sections found in either JSON or text format")
            print(f"[Outline] Content dump:\n{content}")
        return sections or None

    def _generate_slide_bullets(
        self, request: SlidesRequest, section: OutlineSection
    ) -> list[str]:
        prompt_file = PROMPTS_DIR / "slide_content.md"
        if not prompt_file.exists():
            raise FileNotFoundError("Prompt template slide_content.md is missing under prompts/")

        template = prompt_file.read_text(encoding="utf-8")
        prompt = template.format(
            topic=request.topic,
            section_title=section.title,
            style_prompt=request.style_prompt or '专业商务'
        )

        content = self._maybe_generate_text(prompt)
        if not content:
            raise RuntimeError(f"Slide content generation failed for section: {section.title}")
        bullets = [line.lstrip("- ") for line in content.splitlines() if line.strip().startswith("-")]
        if not bullets:
            raise RuntimeError(f"No bullets returned for section: {section.title}")
        return bullets


    def _maybe_generate_text(self, prompt: str, model: ModelConfig | None = None) -> str | None:
        if self.text_provider:
            api_key = model.api_key if model and model.api_key else self.settings.text_api_key
            provider = self.text_provider
            if model:
                provider = DoubaoTextProvider(
                    model=model.model,
                    base_url=self._normalize_url(model.base_url, "default_text_base_url"),
                    api_key=api_key,
                    client=self.text_provider.client,
                )
            if provider.can_call:
                preview = prompt[:120].replace("\n", " ")
                print(f"[Doubao] Attempting text generation | model={provider.model} base_url={provider.base_url} can_call={provider.can_call} prompt_preview={preview}")
                try:
                    return provider.generate(prompt)
                except Exception as exc:
                    print(f"[Doubao] Text generation failed: {type(exc).__name__}: {exc}")
                    return None
            else:
                reason = []
                if not provider.api_key:
                    reason.append("missing API key")
                if not provider._valid_url(provider.base_url):
                    reason.append("invalid base_url")
                print(f"[Doubao] Skipping text generation: {', '.join(reason) if reason else 'unknown reason'}")
        return None

    @staticmethod
    def _load_prompt_template(filename: str) -> str | None:
        path = PROMPTS_DIR / filename
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None

    def _rank_references(self, references: list[ReferenceArticle]) -> list[ReferenceArticle]:
        scored = [
            (ref, self._authority_score(ref.url, ref.source)) for ref in references
        ]
        scored.sort(key=lambda item: item[1], reverse=True)
        ranked: list[ReferenceArticle] = []
        for idx, (ref, _) in enumerate(scored, start=1):
            ranked.append(ref.model_copy(update={"rank": idx}))
        return ranked

    @staticmethod
    def _authority_score(url: str, source_label: str) -> int:
        parsed = urlparse(url)
        host = parsed.netloc
        score = 0
        if "gov" in host:
            score += 100
        if "edu" in host:
            score += 85
        if host.endswith("org"):
            score += 75
        if host.endswith("com") or "media" in host:
            score += 60
        if "blog" in host:
            score -= 5
        if "官方" in source_label:
            score += 10
        return score

    @staticmethod
    def _palette_for_slide(idx: int) -> Palette:
        return Palette(
            primary="#0f172a" if idx == 0 else DEFAULT_PALETTE.primary,
            secondary="#16a34a" if idx == 0 else DEFAULT_PALETTE.secondary,
            accent=DEFAULT_PALETTE.accent,
        )

    @staticmethod
    def _sources_for_slide(idx: int, references: list[ReferenceArticle]) -> list[int]:
        if not references:
            return []
        span = min(3, len(references))
        selected = {
            references[(idx + offset) % len(references)].rank
            for offset in range(span)
        }
        return sorted(selected)

    @staticmethod
    def _reference_index_slide(topic: str, references: list[ReferenceArticle]) -> SlideContent:
        bullets = [f"{ref.rank}. {ref.title} — {ref.url}" for ref in references]
        palette = Palette(
            primary=DEFAULT_PALETTE.primary,
            secondary="#0ea5e9",
            accent=DEFAULT_PALETTE.accent,
        )
        return SlideContent(
            title=f"{topic} · 参考资料索引",
            bullets=bullets,
            palette=palette,
            keywords=f"{topic} · 参考资料",
            style_prompt="参考索引，无水印",
            sources=[ref.rank for ref in references],
        )

    @staticmethod
    def _build_svg_data_url(title: str, style_prompt: str | None, palette: Palette) -> str:
        subtitle = style_prompt or "SeaDream 4.5 风格占位"
        svg = f"""
<svg xmlns='http://www.w3.org/2000/svg' width='960' height='540'>
  <rect width='960' height='540' fill='{palette.primary}' />
  <rect x='60' y='70' width='840' height='140' rx='18' fill='{palette.secondary}' opacity='0.88'/>
  <rect x='60' y='240' width='840' height='200' rx='16' fill='{palette.accent}' opacity='0.16'/>
  <text x='90' y='150' fill='white' font-family='Inter, system-ui' font-size='32' font-weight='700'>{title}</text>
  <text x='90' y='190' fill='white' font-family='Inter, system-ui' font-size='18' opacity='0.9'>{subtitle}</text>
  <circle cx='120' cy='300' r='10' fill='{palette.accent}' opacity='0.9'/>
  <circle cx='170' cy='320' r='8' fill='{palette.accent}' opacity='0.7'/>
  <circle cx='230' cy='280' r='6' fill='{palette.accent}' opacity='0.5'/>
</svg>
"""
        encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
        return f"data:image/svg+xml;base64,{encoded}"

    @staticmethod
    def _build_search_prompt(request: SearchRequest) -> str:
        return (
            f"- 主题: {request.topic}\n"
            f"- 搜索来源提示: {request.source_hint or '自动'}\n"
            f"- 期望条数: {request.limit}\n"
        )

    @staticmethod
    def _build_outline_prompt(request: OutlineRequest) -> str:
        refs_block = "\n".join(
            f"- {ref.rank or idx + 1}. {ref.title} ({ref.source}): {ref.summary[:100]}"
            for idx, ref in enumerate(request.references)
        )
        template = PPTWorkflowService._load_prompt_template("outline.md")
        if not template:
            raise FileNotFoundError("Prompt template outline.md is missing under prompts/")

        return template.format(
            topic=request.topic,
            ref_count=len(request.references),
            refs_block=refs_block,
            max_slides=MAX_SLIDES,
        )


    @staticmethod
    def _build_slide_prompt(request: SlidesRequest, references: list[ReferenceArticle]) -> str:
        ref_lines = "\n".join(
            f"- {ref.rank}. {ref.title} — {ref.url}" for ref in references
        )
        outline_lines = "\n".join(
            f"- {section.title}: {', '.join(section.bullets)}" for section in request.outline
        )
        template = PPTWorkflowService._load_prompt_template("slide_content.md")
        if not template:
            raise FileNotFoundError("Prompt template slide_content.md is missing under prompts/")

        return template.format(
            topic=request.topic,
            outline=outline_lines,
            references=ref_lines,
            style_prompt=request.style_prompt or "默认",
            section_title="{section_title}",
        )

    @staticmethod
    def _build_image_prompt(model: str, base_url: str, watermark: bool, count: int) -> str:
        return (
            f"- 图片模型: {model}\n"
            f"- Base URL: {base_url}\n"
            f"- 图片数量: {count}\n"
            f"- 水印: {'开启' if watermark else '关闭'}\n"
        )
