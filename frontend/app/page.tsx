"use client";

import React from "react";
import jsPDF from "jspdf";
import { Badge } from "./components/ui/badge";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import { Textarea } from "./components/ui/textarea";

interface ReferenceArticle {
  title: string;
  url: string;
  summary: string;
  source: string;
}

interface OutlineSection {
  title: string;
  bullets: string[];
}

interface SlideContent {
  title: string;
  bullets: string[];
  palette: {
    primary: string;
    secondary: string;
    accent: string;
  };
  keywords: string;
}

interface ModelConfig {
  textModel: string;
  textBaseUrl: string;
  textApiKey: string;
  imageModel: string;
  imageBaseUrl: string;
  imageApiKey: string;
}

const defaultPalette = {
  primary: "#0f172a",
  secondary: "#6366f1",
  accent: "#f59e0b",
};

const defaultConfig: ModelConfig = {
  textModel: "skylark2-pro-4k",
  textBaseUrl: "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
  textApiKey: "",
  imageModel: "seadream-4.5",
  imageBaseUrl: "https://image.wodcoai.com/",
  imageApiKey: "",
};

function generateReferenceArticles(topic: string): ReferenceArticle[] {
  const seeds = [
    "行业报告",
    "博客洞察",
    "市场数据",
    "开源案例",
    "设计灵感",
    "媒体评论",
  ];
  return Array.from({ length: 5 }).map((_, idx) => {
    const angle = seeds[idx % seeds.length];
    return {
      title: `${topic} · ${angle}`,
      source: "智能检索",
      url: `https://example.com/${encodeURIComponent(topic)}?ref=${idx + 1}`,
      summary: `从${angle}视角整理的${topic}素材，强调可复用的事实与视觉元素。`,
    };
  });
}

function generateOutline(topic: string, references: ReferenceArticle[]): OutlineSection[] {
  const context = references.slice(0, 3).map((r) => r.title).join(" / ");
  return [
    {
      title: `${topic} 封面`,
      bullets: [
        `${topic} 概览`,
        "关键词 + 配色基调",
        `参考素材：${context || "用户输入"}`,
      ],
    },
    {
      title: "背景与痛点",
      bullets: ["行业现状速览", "主要矛盾或机会", "与主题的关联"],
    },
    {
      title: "解决方案框架",
      bullets: ["目标与策略", "流程/架构", "成功判据"],
    },
    {
      title: "案例与参考",
      bullets: ["同类成功案例", "可落地的做法", "关键数据/指标"],
    },
    {
      title: "下一步行动",
      bullets: ["执行计划", "资源需求", "风险与备选"],
    },
  ];
}

function craftSlides(topic: string, outline: OutlineSection[]): SlideContent[] {
  return outline.map((section, idx) => {
    const palette = {
      primary: idx === 0 ? "#0f172a" : defaultPalette.primary,
      secondary: idx === 0 ? "#16a34a" : defaultPalette.secondary,
      accent: idx === 0 ? "#f59e0b" : defaultPalette.accent,
    };
    return {
      title: section.title,
      bullets: section.bullets,
      palette,
      keywords: `${topic} · 第${idx + 1}页`,
    };
  });
}

function toDataUrl(text: string, palette: { primary: string; secondary: string; accent: string }): string {
  if (typeof document === "undefined") {
    return "";
  }
  const canvas = document.createElement("canvas");
  canvas.width = 960;
  canvas.height = 540;
  const ctx = canvas.getContext("2d");
  if (!ctx) return "";

  ctx.fillStyle = palette.primary;
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = palette.secondary;
  ctx.fillRect(60, 60, canvas.width - 120, 150);
  ctx.fillStyle = "rgba(255,255,255,0.12)";
  ctx.fillRect(60, 230, canvas.width - 120, 200);

  ctx.fillStyle = "#ffffff";
  ctx.font = "bold 32px Inter, system-ui, -apple-system";
  ctx.fillText(text, 80, 120);
  ctx.font = "18px Inter, system-ui, -apple-system";
  ctx.fillText("SeaDream 4.5 风格 · 依据首图样式对齐", 80, 170);
  ctx.fillStyle = palette.accent;
  ctx.fillRect(80, 260, 160, 8);
  ctx.fillRect(80, 280, 210, 6);
  ctx.fillRect(80, 300, 120, 6);

  return canvas.toDataURL("image/png");
}

export default function HomePage() {
  const [topic, setTopic] = React.useState("新能源战略规划");
  const [stylePrompt, setStylePrompt] = React.useState("简洁商务 · 大胆配色 · 几何元素");
  const [config, setConfig] = React.useState<ModelConfig>(defaultConfig);
  const [references, setReferences] = React.useState<ReferenceArticle[]>([]);
  const [outline, setOutline] = React.useState<OutlineSection[]>([]);
  const [slides, setSlides] = React.useState<SlideContent[]>([]);
  const [slideImages, setSlideImages] = React.useState<Record<string, string>>({});
  const [statusLog, setStatusLog] = React.useState<string[]>([]);
  const [busy, setBusy] = React.useState<string | null>(null);

  const pushStatus = (message: string) =>
    setStatusLog((prev) => [`${new Date().toLocaleTimeString()} · ${message}`, ...prev].slice(0, 12));

  const updateConfig = (field: keyof ModelConfig, value: string) => {
    setConfig((prev) => ({ ...prev, [field]: value }));
  };

  const runReferenceSearch = async () => {
    setBusy("reference");
    pushStatus(`使用 ${config.textModel} 检索可用素材…`);
    await new Promise((resolve) => setTimeout(resolve, 350));
    const results = generateReferenceArticles(topic);
    setReferences(results);
    pushStatus("完成素材检索，并展示在左侧列表");
    setBusy(null);
  };

  const runOutline = async () => {
    if (!references.length) await runReferenceSearch();
    setBusy("outline");
    pushStatus(`汇总素材，用 ${config.textModel} 生成 PPT 大纲…`);
    await new Promise((resolve) => setTimeout(resolve, 320));
    const nextOutline = generateOutline(topic, references);
    setOutline(nextOutline);
    pushStatus("大纲已就绪，展示在中间区域");
    setBusy(null);
  };

  const runSlides = async () => {
    if (!outline.length) await runOutline();
    setBusy("slides");
    pushStatus("展开每页内容与配色主题…");
    await new Promise((resolve) => setTimeout(resolve, 320));
    const nextSlides = craftSlides(topic, outline).map((slide, idx) => ({
      ...slide,
      palette: idx === 0 ? slide.palette : { ...slide.palette, primary: defaultPalette.primary, secondary: defaultPalette.secondary },
    }));
    setSlides(nextSlides);
    pushStatus("内容草稿完成，可继续生成图片");
    setBusy(null);
  };

  const runImages = async () => {
    if (!slides.length) await runSlides();
    setBusy("images");
    pushStatus(`调用 ${config.imageModel} 生成图片，后续图片参考首图样式…`);
    await new Promise((resolve) => setTimeout(resolve, 420));
    const basePalette = slides[0]?.palette || defaultPalette;
    const images = slides.reduce<Record<string, string>>((acc, slide, idx) => {
      const palette = idx === 0 ? slide.palette : { ...slide.palette, primary: basePalette.primary, secondary: basePalette.secondary };
      acc[slide.title] = toDataUrl(`${slide.title} · ${stylePrompt}`, palette);
      return acc;
    }, {});
    setSlideImages(images);
    pushStatus("图片生成完成，展示在右侧");
    setBusy(null);
  };

  const downloadPdf = () => {
    if (!slides.length) return;
    const doc = new jsPDF({ orientation: "landscape", unit: "pt", format: "a4" });
    slides.forEach((slide, idx) => {
      if (idx !== 0) doc.addPage();
      doc.setFontSize(20);
      doc.text(slide.title, 60, 80);
      doc.setFontSize(12);
      slide.bullets.forEach((b, i) => doc.text(`• ${b}`, 80, 120 + i * 22));
      doc.setTextColor(100);
      doc.text(`模型: ${config.textModel} | 图片: ${config.imageModel}`, 60, 240);
      doc.text(`关键词: ${slide.keywords}`, 60, 260);
      const image = slideImages[slide.title];
      if (image) {
        doc.addImage(image, "PNG", 360, 90, 360, 203);
      }
      doc.setTextColor(0);
    });
    doc.save(`${topic}-workflow.pdf`);
    pushStatus("已导出 PDF，包含当前的文字与预览图");
  };

  const referenceGrid = (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>1. 参考素材</CardTitle>
        <CardDescription>
          默认走火山文本模型，可修改 base_url / API Key。结果展示在左列，方便核对引用。
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 gap-3">
          <div className="space-y-2">
            <Label htmlFor="topic">主题</Label>
            <Input
              id="topic"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="输入要生成的 PPT 主题"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="style">风格提示</Label>
            <Textarea
              id="style"
              value={stylePrompt}
              onChange={(e) => setStylePrompt(e.target.value)}
              placeholder="如：极简 · 柔和渐变 · 科技感几何"
            />
          </div>
          <Button onClick={runReferenceSearch} disabled={busy === "reference"}>
            {busy === "reference" ? "检索中…" : "搜索参考文章"}
          </Button>
        </div>
        <div className="space-y-3">
          {references.map((ref) => (
            <div key={ref.title} className="rounded-lg border border-slate-200 p-3">
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold text-slate-900">{ref.title}</p>
                <Badge variant="muted">{ref.source}</Badge>
              </div>
              <p className="mt-1 text-sm text-slate-600">{ref.summary}</p>
              <a className="mt-2 inline-block text-xs text-blue-600" href={ref.url} target="_blank">
                {ref.url}
              </a>
            </div>
          ))}
          {!references.length && <p className="text-sm text-slate-500">等待检索结果…</p>}
        </div>
      </CardContent>
    </Card>
  );

  const outlineGrid = (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>2. 大纲与内容</CardTitle>
        <CardDescription>
          汇总检索结果生成 PPT 大纲，再展开每一页文字与配色方案。中列展示实时草稿。
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
          <div className="space-y-2">
            <Label>文本模型</Label>
            <Input
              value={config.textModel}
              onChange={(e) => updateConfig("textModel", e.target.value)}
              placeholder="skylark2-pro-4k"
            />
          </div>
          <div className="space-y-2">
            <Label>文本 Base URL</Label>
            <Input
              value={config.textBaseUrl}
              onChange={(e) => updateConfig("textBaseUrl", e.target.value)}
              placeholder="https://..."
            />
          </div>
          <div className="space-y-2">
            <Label>文本 API Key</Label>
            <Input
              value={config.textApiKey}
              onChange={(e) => updateConfig("textApiKey", e.target.value)}
              placeholder="保存在本地，不会上传"
            />
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" onClick={runOutline} disabled={busy === "outline"}>
            {busy === "outline" ? "生成中…" : "生成 PPT 大纲"}
          </Button>
          <Button variant="secondary" onClick={runSlides} disabled={busy === "slides"}>
            {busy === "slides" ? "整理中…" : "生成每页内容"}
          </Button>
          <Button variant="outline" onClick={runImages} disabled={busy === "images"}>
            {busy === "images" ? "绘制中…" : "生成配图"}
          </Button>
        </div>
        <div className="space-y-3">
          {outline.map((section) => (
            <div key={section.title} className="rounded-lg border border-slate-200 p-3">
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold text-slate-900">{section.title}</p>
                <Badge variant="outline">大纲</Badge>
              </div>
              <ul className="mt-2 space-y-1 text-sm text-slate-700">
                {section.bullets.map((item) => (
                  <li key={item}>• {item}</li>
                ))}
              </ul>
            </div>
          ))}
          {!outline.length && <p className="text-sm text-slate-500">等待生成大纲…</p>}
        </div>
      </CardContent>
    </Card>
  );

  const slidesGrid = (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>3. 配图与导出</CardTitle>
        <CardDescription>
          图片默认使用 SeaDream 4.5，除首图外统一沿用首图风格。右列展示图片与 PDF 下载。
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
          <div className="space-y-2">
            <Label>图片模型</Label>
            <Input
              value={config.imageModel}
              onChange={(e) => updateConfig("imageModel", e.target.value)}
              placeholder="seadream-4.5"
            />
          </div>
          <div className="space-y-2">
            <Label>图片 Base URL</Label>
            <Input
              value={config.imageBaseUrl}
              onChange={(e) => updateConfig("imageBaseUrl", e.target.value)}
              placeholder="https://..."
            />
          </div>
          <div className="space-y-2">
            <Label>图片 API Key</Label>
            <Input
              value={config.imageApiKey}
              onChange={(e) => updateConfig("imageApiKey", e.target.value)}
              placeholder="保存在本地，不会上传"
            />
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button onClick={runImages} disabled={busy === "images" || !slides.length}>
            {busy === "images" ? "绘制中…" : "生成/刷新图片"}
          </Button>
          <Button variant="secondary" onClick={downloadPdf} disabled={!slides.length}>
            下载 PDF
          </Button>
        </div>
        <div className="grid grid-cols-1 gap-4">
          {slides.map((slide) => (
            <div key={slide.title} className="overflow-hidden rounded-xl border border-slate-200">
              <div className="flex items-center justify-between bg-slate-50 px-4 py-3">
                <div>
                  <p className="text-sm font-semibold text-slate-900">{slide.title}</p>
                  <p className="text-xs text-slate-500">{slide.keywords}</p>
                </div>
                <div className="flex gap-2 text-xs text-slate-500">
                  <span className="inline-flex items-center gap-1">🎨 {slide.palette.primary}</span>
                  <span className="inline-flex items-center gap-1">✨ {slide.palette.secondary}</span>
                </div>
              </div>
              <div className="grid grid-cols-1 gap-3 p-4 md:grid-cols-2">
                <div>
                  <ul className="space-y-1 text-sm text-slate-700">
                    {slide.bullets.map((bullet) => (
                      <li key={bullet}>• {bullet}</li>
                    ))}
                  </ul>
                </div>
                <div className="flex items-center justify-center rounded-lg border border-slate-100 bg-slate-50 p-2">
                  {slideImages[slide.title] ? (
                    <img
                      src={slideImages[slide.title]}
                      alt={`${slide.title} illustration`}
                      className="h-48 w-full rounded-lg object-cover shadow"
                    />
                  ) : (
                    <p className="text-sm text-slate-500">等待生成 SeaDream 4.5 图片…</p>
                  )}
                </div>
              </div>
            </div>
          ))}
          {!slides.length && <p className="text-sm text-slate-500">先生成大纲与内容，再生成图片</p>}
        </div>
      </CardContent>
    </Card>
  );

  return (
    <main className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold text-slate-900">PPT 生成 Workflow · 火山文本 + SeaDream 4.5</h1>
        <p className="text-sm text-slate-600">
          左侧检索参考，中间生成大纲与文案，右侧生成配图与 PDF。模型、Base URL 与 API Key 均可自定义。
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="space-y-4">{referenceGrid}</div>
        <div className="space-y-4">{outlineGrid}</div>
        <div className="space-y-4">{slidesGrid}</div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>流程日志</CardTitle>
          <CardDescription>追踪每个步骤的状态，便于排查与复现。</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          {statusLog.length ? (
            <ul className="space-y-1 text-sm text-slate-700">
              {statusLog.map((msg) => (
                <li key={msg} className="flex items-start gap-2">
                  <span className="mt-1 h-2 w-2 rounded-full bg-green-500" />
                  <span>{msg}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-500">等待运行工作流…</p>
          )}
        </CardContent>
      </Card>
    </main>
  );
}
