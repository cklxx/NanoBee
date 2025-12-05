from __future__ import annotations

import base64
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from ..config import Settings
from .providers import DoubaoTextProvider, SeaDreamImageProvider
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

    def read_notebook(self, topic: str, stage: str | None = None) -> PromptNotebookResponse:
        notebook = self._notebook(topic)
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
        notebook = self._notebook(request.topic)
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
        notebook = self._notebook(request.topic)
        notebook.save_prompt(
            "outline",
            self._build_outline_prompt(request),
        )

        top_refs = request.references[:3]
        context = "、".join(ref.title for ref in top_refs) or "用户输入"
        prompt_outline = self._generate_outline_from_model(request, context)
        outline = prompt_outline or [
            self._outline_section(
                f"{request.topic} 封面",
                [
                    f"主题总览：{request.topic}",
                    f"关键词与配色：{DEFAULT_PALETTE.primary}/{DEFAULT_PALETTE.secondary}",
                    f"参考素材：{context}",
                ],
            ),
            self._outline_section("机会与痛点", ["市场现状", "主要挑战", "用户痛点"]),
            self._outline_section("解决方案", ["核心主张", "架构与流程", "差异化亮点"]),
            self._outline_section("案例与数据", ["行业案例", "关键指标", "可执行步骤"]),
            self._outline_section("路径与行动", ["里程碑", "资源/风险", "下一步计划"]),
        ]

        return OutlineResponse(topic=request.topic, outline=outline)

    def _outline_section(self, title: str, bullets: list[str]) -> OutlineSection:
        return OutlineSection(title=title, bullets=bullets)

    def generate_slides(self, request: SlidesRequest) -> SlidesResponse:
        notebook = self._notebook(request.topic)
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
        for idx, slide in enumerate(request.slides):
            palette = slide.palette
            if idx > 0:
                palette = Palette(
                    primary=base_palette.primary,
                    secondary=base_palette.secondary,
                    accent=palette.accent,
                )
            data_url = self._build_data_url(slide, palette, watermark, model, base_url, api_key)
            images.append(
                SlideImage(
                    title=slide.title,
                    style_seed=slide.keywords,
                    data_url=data_url,
                    model=model,
                    base_url=base_url,
                    watermark=watermark,
                )
            )

        topic = request.topic or (request.slides[0].title if request.slides else "images")
        notebook = self._notebook(topic)
        notebook.save_prompt(
            "images",
            self._build_image_prompt(model, base_url, watermark, len(request.slides)),
        )
        return ImagesResponse(images=images)

    def _notebook(self, topic: str) -> PromptNotebook:
        return PromptNotebook(root=self.notebook_root, topic=topic)

    def _build_data_url(
        self,
        slide: SlideContent,
        palette: Palette,
        watermark: bool,
        model: str,
        base_url: str,
        api_key: str | None,
    ) -> str:
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
        return self._build_content_svg(slide, palette)

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
        self, request: OutlineRequest, context: str
    ) -> list[OutlineSection] | None:
        prompt = (
            f"为主题《{request.topic}》生成 5 章 PPT 大纲，每章含 3 条 bullet。"
            f"参考素材：{context}。以 '章节：' 开头写章节标题，后面逐行列出 '- ' 开头的要点。"
        )
        content = self._maybe_generate_text(prompt, request.text_model)
        if not content:
            return None
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
        return sections or None

    def _generate_slide_bullets(
        self, request: SlidesRequest, section: OutlineSection
    ) -> list[str]:
        prompt_file = PROMPTS_DIR / "slide_content.md"
        if not prompt_file.exists():
            # Fallback if file not found
            prompt = (
                f"主题《{request.topic}》，章节《{section.title}》。"
                f"参考提示：{request.style_prompt or '商务简洁'}。"
                "请输出 3-4 条要点，每条不超过 30 字，以 '- ' 开头。"
            )
        else:
            template = prompt_file.read_text(encoding="utf-8")
            prompt = template.format(
                topic=request.topic,
                section_title=section.title,
                style_prompt=request.style_prompt or '专业商务'
            )

        content = self._maybe_generate_text(prompt)
        if not content:
            return section.bullets
        bullets = [line.lstrip("- ") for line in content.splitlines() if line.strip().startswith("-")]
        return bullets or section.bullets


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
                try:
                    return provider.generate(prompt)
                except Exception:
                    return None
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
        
        prompt_file = PROMPTS_DIR / "outline.md"
        if prompt_file.exists():
            template = prompt_file.read_text(encoding="utf-8")
            return template.format(
                topic=request.topic,
                ref_count=len(request.references),
                refs_block=refs_block,
                max_slides=MAX_SLIDES
            )
            
        # Fallback
        return f"""请根据以下参考资料，为主题"{request.topic}"生成一个专业、有深度的PPT大纲。

## 参考资料（共{len(request.references)}条）
{refs_block}

## PPT大纲要求
请生成{MAX_SLIDES}页的大纲。"""


    @staticmethod
    def _build_slide_prompt(request: SlidesRequest, references: list[ReferenceArticle]) -> str:
        ref_lines = "\n".join(
            f"- {ref.rank}. {ref.title} — {ref.url}" for ref in references
        )
        outline_lines = "\n".join(
            f"- {section.title}: {', '.join(section.bullets)}" for section in request.outline
        )
        return (
            f"- 主题: {request.topic}\n"
            f"- 风格: {request.style_prompt or '默认'}\n"
            f"- 文本模型: {request.text_model.model if request.text_model else '默认'}\n"
            f"- 参考: \n{ref_lines}\n"
            f"- 大纲: \n{outline_lines}\n"
            f"- 总页数上限: {MAX_SLIDES}\n"
        )

    @staticmethod
    def _build_image_prompt(model: str, base_url: str, watermark: bool, count: int) -> str:
        return (
            f"- 图片模型: {model}\n"
            f"- Base URL: {base_url}\n"
            f"- 图片数量: {count}\n"
            f"- 水印: {'开启' if watermark else '关闭'}\n"
        )
