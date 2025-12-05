"use client";

import React from "react";
import jsPDF from "jspdf";
import { Badge } from "./components/ui/badge";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import { Textarea } from "./components/ui/textarea";
import Link from "next/link";

const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

interface ReferenceArticle {
  title: string;
  url: string;
  summary: string;
  source: string;
  rank?: number;
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
  style_prompt?: string;
  sources?: number[];
}

interface SlideImage {
  title: string;
  data_url: string;
  style_seed: string;
  model: string;
}

const MAX_SAVED_PROJECTS = 10;

export default function HomePage() {
  const [topic, setTopic] = React.useState("人工智能发展历史");
  const [stylePrompt, setStylePrompt] = React.useState("简洁商务 · 大胆配色 · 几何元素");
  const [references, setReferences] = React.useState<ReferenceArticle[]>([]);
  const [outline, setOutline] = React.useState<OutlineSection[]>([]);
  const [slides, setSlides] = React.useState<SlideContent[]>([]);
  const [slideImages, setSlideImages] = React.useState<SlideImage[]>([]);
  const [statusLog, setStatusLog] = React.useState<string[]>([]);
  const [busy, setBusy] = React.useState<string | null>(null);
  const [currentSlideIndex, setCurrentSlideIndex] = React.useState(0);
  const [expandedRefs, setExpandedRefs] = React.useState<Set<number>>(new Set());
  const [apiKey, setApiKey] = React.useState(""); // 用户自定义 API Key
  const [sessionId, setSessionId] = React.useState<string>(() => crypto.randomUUID());

  // 加载 API Key
  React.useEffect(() => {
    const key = localStorage.getItem('nanobee_api_key');
    if (key) setApiKey(key);
  }, []);

  // 保存 API Key
  const handleApiKeyChange = (value: string) => {
    setApiKey(value);
    localStorage.setItem('nanobee_api_key', value);
  };

  const resetSession = () => {
    const next = crypto.randomUUID();
    setSessionId(next);
    pushStatus(`✓ 已切换到新的会话 (${next.slice(0, 8)})`);
  };

  // PPT项目管理
  interface SavedProject {
    id: string;
    topic: string;
    stylePrompt: string;
    timestamp: number;
    references: ReferenceArticle[];
    outline: OutlineSection[];
    slides: SlideContent[];
    slideImages: SlideImage[];
  }

  const [savedProjects, setSavedProjects] = React.useState<SavedProject[]>([]);
  const [currentProjectId, setCurrentProjectId] = React.useState<string | null>(null);
  const [showHistory, setShowHistory] = React.useState(false);

  // 加载已保存的项目列表
  React.useEffect(() => {
    const saved = localStorage.getItem('nanobee_projects');
    if (saved) {
      try {
        setSavedProjects(JSON.parse(saved));
      } catch (e) {
        console.error('Failed to load saved projects', e);
      }
    }
  }, []);

  // 保存当前项目
  // 自动保存逻辑
  React.useEffect(() => {
    // 只有当有实质内容时才保存
    if (!topic && !slides.length) return;

    const timer = setTimeout(() => {
      saveProject();
    }, 1000); // 1秒防抖

    return () => clearTimeout(timer);
  }, [topic, stylePrompt, references, outline, slides, slideImages]);

  const saveProject = () => {
    const timestamp = Date.now();
    let id = currentProjectId;

    // 如果没有ID，创建一个新ID
    if (!id) {
      // 只有在真的已经在创作时才创建新ID
      if (topic || slides.length) {
        id = timestamp.toString();
        setCurrentProjectId(id);
      } else {
        return;
      }
    }

    const project: SavedProject = {
      id: id!,
      topic,
      stylePrompt,
      timestamp,
      references,
      outline,
      slides,
      // Avoid blowing up localStorage with base64 images
      slideImages: slideImages.map((img) => ({
        ...img,
        data_url: "",
      })),
    };

    setSavedProjects(prev => {
      const index = prev.findIndex(p => p.id === project.id);
      let newProjects;
      if (index >= 0) {
        // 更新现有项目
        newProjects = [...prev];
        newProjects[index] = project;
      } else {
        // 新增项目
        newProjects = [project, ...prev];
      }
      newProjects = newProjects.slice(0, MAX_SAVED_PROJECTS);
      try {
        localStorage.setItem('nanobee_projects', JSON.stringify(newProjects));
      } catch (err) {
        console.warn('Failed to save projects', err);
        setStatusLog((prevLog) => [`${new Date().toLocaleTimeString()} · ✗ 保存失败：存储空间不足`, ...prevLog].slice(0, 20));
        return prev;
      }
      return newProjects;
    });
  };

  // 加载已保存的项目
  const loadProject = (project: SavedProject) => {
    setTopic(project.topic);
    setStylePrompt(project.stylePrompt);
    setReferences(project.references);
    setOutline(project.outline);
    setSlides(project.slides);
    setSlideImages(project.slideImages);
    setCurrentSlideIndex(0);
    setSessionId(crypto.randomUUID()); // 新会话，避免历史堆积
    setCurrentProjectId(project.id); // 设置当前项目ID
    setShowHistory(false);
    pushStatus(`✓ 已加载项目：${project.topic}`);
  };

  // 删除项目
  const deleteProject = (id: string) => {
    const newProjects = savedProjects.filter(p => p.id !== id);
    setSavedProjects(newProjects);
    localStorage.setItem('nanobee_projects', JSON.stringify(newProjects));
    if (id === currentProjectId) {
      setCurrentProjectId(null); // 如果删除了当前项目，重置ID
    }
    pushStatus('✓ 已删除项目');
  };

  const pushStatus = (message: string) =>
    setStatusLog((prev) => [`${new Date().toLocaleTimeString()} · ${message}`, ...prev].slice(0, 20));

  const runReferenceSearch = async () => {
    setBusy("reference");
    pushStatus(`正在搜索关于 "${topic}" 的参考资料...`);
    try {
      const response = await fetch(`${apiBase}/api/ppt/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic, limit: 6, session_id: sessionId }),
      });
      if (!response.ok) throw new Error(`搜索失败: ${response.statusText}`);
      const data = await response.json();
      setReferences(data.references || []);
      pushStatus(`✓ 找到 ${data.references?.length || 0} 个参考资料`);
    } catch (error: any) {
      pushStatus(`✗ 搜索失败: ${error.message}`);
    } finally {
      setBusy(null);
    }
  };

  const runOutline = async () => {
    if (!references.length) await runReferenceSearch();
    setBusy("outline");
    pushStatus(`正在生成 PPT 大纲...`);
    try {
      const response = await fetch(`${apiBase}/api/ppt/outline`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic,
          references,
          session_id: sessionId,
          text_model: apiKey ? { model: "doubao-seed-1-6-251015", base_url: "", api_key: apiKey } : undefined
        }),
      });
      if (!response.ok) throw new Error(`大纲生成失败: ${response.statusText}`);
      const data = await response.json();
      setOutline(data.outline || []);
      pushStatus(`✓ 大纲生成完成，共 ${data.outline?.length || 0} 个部分`);
    } catch (error: any) {
      pushStatus(`✗ 大纲生成失败: ${error.message}`);
    } finally {
      setBusy(null);
    }
  };

  const runSlides = async () => {
    if (!outline.length) await runOutline();
    setBusy("slides");
    pushStatus(`正在生成每页PPT内容...`);
    try {
      const response = await fetch(`${apiBase}/api/ppt/slides`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic,
          outline,
          references,
          style_prompt: stylePrompt,
          session_id: sessionId,
          text_model: apiKey ? { model: "doubao-seed-1-6-251015", base_url: "", api_key: apiKey } : undefined
        }),
      });
      if (!response.ok) throw new Error(`幻灯片生成失败: ${response.statusText}`);
      const data = await response.json();
      setSlides(data.slides || []);
      pushStatus(`✓ 生成了 ${data.slides?.length || 0} 页幻灯片`);
    } catch (error: any) {
      pushStatus(`✗ 幻灯片生成失败: ${error.message}`);
    } finally {
      setBusy(null);
    }
  };

  const runImages = async () => {
    if (!slides.length) await runSlides();
    setBusy("images");
    pushStatus(`调用 SeaDream 生成 PPT 页面，这可能需要一些时间...`);
    try {
      const response = await fetch(`${apiBase}/api/ppt/images`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic,
          slides,
          watermark: false,
          session_id: sessionId,
          image_model: apiKey ? { model: "doubao-seedream-4-5-251128", base_url: "", api_key: apiKey } : undefined
        }),
      });
      if (!response.ok) throw new Error(`PPT 页面生成失败: ${response.statusText}`);
      const data = await response.json();
      setSlideImages(data.images || []);
      pushStatus(`✓ 成功生成 ${data.images?.length || 0} 页 PPT 视觉效果`);
    } catch (error: any) {
      pushStatus(`✗ PPT 页面生成失败: ${error.message}`);
    } finally {
      setBusy(null);
    }
  };

  const downloadPdf = () => {
    if (!slides.length) return;
    const doc = new jsPDF({ orientation: "landscape", unit: "pt", format: "a4" });
    slides.forEach((slide, idx) => {
      if (idx !== 0) doc.addPage();
      doc.setFontSize(24);
      doc.text(slide.title, 60, 80);
      doc.setFontSize(14);
      slide.bullets.forEach((b, i) => doc.text(`• ${b}`, 80, 130 + i * 24));
      const image = slideImages.find((img) => img.title === slide.title);
      if (image?.data_url) {
        try {
          doc.addImage(image.data_url, "PNG", 400, 90, 320, 180);
        } catch (e) {
          console.error("Failed to add image to PDF", e);
        }
      }
    });
    doc.save(`${topic}.pdf`);
    pushStatus("✓ PDF 已导出");
  };

  const currentSlide = slides[currentSlideIndex];
  const currentImage = slideImages.find((img) => img.title === currentSlide?.title);

  return (
    <div className="flex h-screen bg-slate-50">
      {/* 左侧控制面板 */}
      <div className="w-1/3 border-r border-slate-200 bg-white overflow-y-auto">
        <div className="p-6 space-y-6">
          {/* 标题与项目管理 */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-slate-700">
                  NanoBee PPT
                </h1>
                <p className="text-sm text-slate-500">AI 驱动的 PPT 生成工作流</p>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <Badge variant="secondary" className="text-xs">
                Session {sessionId.slice(0, 8)}
              </Badge>
              <Button size="sm" variant="outline" onClick={resetSession}>
                新会话
              </Button>
            </div>
            {/* 项目管理按钮 */}
            <div className="flex gap-2">
              <Button
                onClick={() => setShowHistory(!showHistory)}
                variant="outline"
                className="flex-1 text-sm"
              >
                📚 历史记录 ({savedProjects.length})
              </Button>

            </div>
          </div>

          {/* 历史记录列表 */}
          {showHistory && (
            <Card className="border-slate-300">
              <CardHeader>
                <CardTitle className="text-base">已保存的项目</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 max-h-64 overflow-y-auto">
                {savedProjects.length === 0 ? (
                  <p className="text-sm text-slate-400 text-center py-4">暂无保存的项目</p>
                ) : (
                  savedProjects.map(project => (
                    <div key={project.id} className="flex items-center gap-2 p-3 border border-slate-200 rounded-lg hover:bg-slate-50">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm truncate">{project.topic}</p>
                        <p className="text-xs text-slate-400">
                          {new Date(project.timestamp).toLocaleString('zh-CN')}
                        </p>
                      </div>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => loadProject(project)}
                        className="text-xs"
                      >
                        加载
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => deleteProject(project.id)}
                        className="text-xs text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        删除
                      </Button>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          )}

          {/* 主题输入 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">1. 主题设置</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="topic">PPT 主题</Label>
                <Input
                  id="topic"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="例如：人工智能发展历史"
                  className="font-medium"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="style">风格描述</Label>
                <Textarea
                  id="style"
                  value={stylePrompt}
                  onChange={(e) => setStylePrompt(e.target.value)}
                  placeholder="例如：极简 · 柔和渐变 · 科技感"
                  rows={2}
                />
              </div>
            </CardContent>
          </Card>

          {/* 操作按钮 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">2. 生成流程</CardTitle>
              <CardDescription>按顺序执行各个步骤</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button
                onClick={runReferenceSearch}
                disabled={busy !== null}
                className="w-full bg-slate-600 hover:bg-slate-700 text-white"
              >
                {busy === "reference" ? "搜索中..." : references.length > 0 ? "✓ 已搜索参考资料" : "① 搜索参考资料"}
              </Button>
              <Button
                onClick={runOutline}
                disabled={busy !== null}
                className="w-full bg-slate-600 hover:bg-slate-700 text-white"
              >
                {busy === "outline" ? "生成中..." : outline.length > 0 ? "✓ 已生成大纲" : "② 生成 PPT 大纲"}
              </Button>
              <Button
                onClick={runSlides}
                disabled={busy !== null}
                className="w-full bg-slate-600 hover:bg-slate-700 text-white"
              >
                {busy === "slides" ? "生成中..." : slides.length > 0 ? "✓ 已生成内容" : "③ 生成每页内容"}
              </Button>
              <Button
                onClick={runImages}
                disabled={!!busy || !slides.length}
                className="w-full bg-slate-600 hover:bg-slate-700 text-white"
              >
                {busy === "images" ? "生成中..." : slideImages.length > 0 ? "✓ 已生成页面" : "④ 生成 PPT 页面"}
              </Button>
              <div className="border-t pt-3 mt-3">
                <Button
                  onClick={downloadPdf}
                  disabled={!slides.length}
                  className="w-full bg-slate-500 hover:bg-slate-600 text-white"
                  variant="outline"
                >
                  📄 导出 PDF
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* 参考资料预览 */}
          {references.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">参考资料 ({references.length})</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 max-h-64 overflow-y-auto">
                {references.map((ref, idx) => {
                  const isExpanded = expandedRefs.has(idx);
                  const toggleExpand = () => {
                    const newSet = new Set(expandedRefs);
                    if (isExpanded) {
                      newSet.delete(idx);
                    } else {
                      newSet.add(idx);
                    }
                    setExpandedRefs(newSet);
                  };

                  return (
                    <div
                      key={idx}
                      className="text-sm p-3 rounded bg-slate-50 border border-slate-200 hover:bg-slate-100 transition cursor-pointer"
                      onClick={toggleExpand}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <p className="font-medium text-slate-900 flex-1">{ref.title}</p>
                        <Badge variant="outline" className="text-xs flex-shrink-0">{ref.source}</Badge>
                      </div>
                      {isExpanded && (
                        <div className="mt-2 pt-2 border-t border-slate-200 space-y-2">
                          <p className="text-xs text-slate-600">{ref.summary}</p>
                          <a
                            href={ref.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-blue-600 hover:text-blue-700 underline block"
                            onClick={(e) => e.stopPropagation()}
                          >
                            查看来源 →
                          </a>
                        </div>
                      )}
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          )}

          {/* 流程日志 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">流程日志</CardTitle>
            </CardHeader>
            <CardContent className="space-y-1 max-h-64 overflow-y-auto">
              {statusLog.length > 0 ? (
                statusLog.map((msg, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-xs">
                    <span className="mt-1 h-1.5 w-1.5 rounded-full bg-indigo-500 flex-shrink-0" />
                    <span className="text-slate-600">{msg}</span>
                  </div>
                ))
              ) : (
                <p className="text-sm text-slate-400">等待开始...</p>
              )}
            </CardContent>
          </Card>
          {/* API Key 设置 */}
          <div className="p-4 border-t border-slate-200 bg-white sticky bottom-0">
            <Label className="text-xs font-semibold text-slate-500 mb-2 block">
              自定义 API Key (可选)
            </Label>
            <Input
              type="password"
              placeholder="sk-..."
              value={apiKey}
              onChange={(e) => handleApiKeyChange(e.target.value)}
              className="mb-2 text-xs h-8"
            />
            <div className="flex justify-between items-center text-[10px] text-slate-400">
              <span>共用于 Doubao/SeaDream</span>
              <Link
                href="/guide/volcengine"
                target="_blank"
                className="text-blue-500 hover:underline flex items-center gap-1"
              >
                ❓ 如何获取 Key
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* 右侧 PPT 展示区 */}
      <div className="flex-1 flex flex-col bg-slate-100">
        {/* 显示逻辑：图片 > 内容 > 大纲 > 空状态 */}
        {slideImages.length > 0 ? (
          /* 图片模式 - 最终版本 */
          <>
            <div className="flex-1 flex items-center justify-between px-8 py-4">
              {/* 左侧导航按钮 */}
              <button
                onClick={() => setCurrentSlideIndex(Math.max(0, currentSlideIndex - 1))}
                disabled={currentSlideIndex === 0}
                className="bg-slate-200 hover:bg-slate-300 disabled:opacity-30 disabled:cursor-not-allowed text-slate-700 rounded-full p-4 transition shadow-lg z-10"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>

              {/* PPT内容区 */}
              <div className="relative flex-1 mx-4 aspect-video shadow-xl animate-fade-in">
                <div
                  className="absolute inset-0 rounded-2xl shadow-2xl overflow-hidden"
                  style={{ backgroundColor: currentSlide?.palette?.primary || "#0f172a" }}
                >
                  {currentImage?.data_url ? (
                    <img
                      src={currentImage.data_url}
                      alt={currentSlide?.title}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <div className="text-center space-y-4 p-12">
                        <h2 className="text-5xl font-bold text-white">{currentSlide?.title}</h2>
                        <div className="space-y-3 text-white text-2xl">
                          {currentSlide?.bullets.map((bullet, i) => (
                            <p key={i}>• {bullet}</p>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* 右侧导航按钮 */}
              <button
                onClick={() => setCurrentSlideIndex(Math.min(slides.length - 1, currentSlideIndex + 1))}
                disabled={currentSlideIndex === slides.length - 1}
                className="bg-slate-200 hover:bg-slate-300 disabled:opacity-30 disabled:cursor-not-allowed text-slate-700 rounded-full p-4 transition shadow-lg z-10"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>

            {/* 缩略图导航 */}
            <div className="border-t border-slate-300 bg-white p-4">
              <div className="flex gap-3 overflow-x-auto pb-2">
                {slides.map((slide, idx) => {
                  const img = slideImages.find((i) => i.title === slide.title);
                  return (
                    <button
                      key={idx}
                      onClick={() => setCurrentSlideIndex(idx)}
                      className={`flex-shrink-0 w-48 aspect-video rounded-lg overflow-hidden border-2 transition ${currentSlideIndex === idx
                        ? "border-slate-400 ring-2 ring-slate-400/30"
                        : "border-slate-300 hover:border-slate-400"
                        }`}
                      style={{ backgroundColor: slide.palette?.primary || "#0f172a" }}
                    >
                      {img?.data_url ? (
                        <img src={img.data_url} alt={slide.title} className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full p-3 flex flex-col justify-between">
                          <p className="text-white text-xs font-semibold line-clamp-2">{slide.title}</p>
                          <p className="text-white text-xs opacity-50">{idx + 1}</p>
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          </>
        ) : slides.length > 0 ? (
          /* 内容模式 - 详细版本 */
          <>
            <div className="flex-1 flex items-center justify-between px-8 py-4">
              <button
                onClick={() => setCurrentSlideIndex(Math.max(0, currentSlideIndex - 1))}
                disabled={currentSlideIndex === 0}
                className="bg-slate-200 hover:bg-slate-300 disabled:opacity-30 disabled:cursor-not-allowed text-slate-700 rounded-full p-4 transition shadow-lg z-10"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <div className="relative flex-1 mx-4 aspect-video shadow-xl animate-fade-in">
                <div
                  className="absolute inset-0 rounded-2xl shadow-2xl overflow-hidden p-12 flex flex-col justify-between"
                  style={{
                    background: `linear-gradient(135deg, ${currentSlide?.palette?.primary || '#1e293b'} 0%, ${currentSlide?.palette?.secondary || '#334155'} 100%)`
                  }}
                >
                  <div>
                    <h2 className="text-5xl font-bold text-white mb-8">{currentSlide?.title}</h2>
                    <div className="space-y-4">
                      {currentSlide?.bullets.map((bullet, i) => (
                        <div key={i} className="flex items-start gap-4">
                          <div className="w-2 h-2 rounded-full bg-white mt-3 flex-shrink-0"></div>
                          <p className="text-white text-2xl leading-relaxed">{bullet}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-white text-sm opacity-60">
                    <span>{currentSlide?.keywords}</span>
                    <span>{currentSlideIndex + 1} / {slides.length}</span>
                  </div>
                </div>
              </div>
              <button
                onClick={() => setCurrentSlideIndex(Math.min(slides.length - 1, currentSlideIndex + 1))}
                disabled={currentSlideIndex === slides.length - 1}
                className="bg-slate-200 hover:bg-slate-300 disabled:opacity-30 disabled:cursor-not-allowed text-slate-700 rounded-full p-4 transition shadow-lg z-10"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>

            {/* 缩略图导航 */}
            <div className="border-t border-slate-300 bg-white p-4">
              <div className="flex gap-3 overflow-x-auto pb-2">
                {slides.map((slide, idx) => (
                  <button
                    key={idx}
                    onClick={() => setCurrentSlideIndex(idx)}
                    className={`flex-shrink-0 w-48 aspect-video rounded-lg overflow-hidden border-2 transition p-3 ${currentSlideIndex === idx
                      ? "border-slate-400 ring-2 ring-slate-400/30"
                      : "border-slate-300 hover:border-slate-400"
                      }`}
                    style={{
                      background: `linear-gradient(135deg, ${slide.palette?.primary || '#1e293b'} 0%, ${slide.palette?.secondary || '#334155'} 100%)`
                    }}
                  >
                    <div className="flex flex-col justify-between h-full">
                      <p className="text-white text-xs font-semibold line-clamp-2">{slide.title}</p>
                      <p className="text-white text-xs opacity-50">{idx + 1}</p>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </>
        ) : outline.length > 0 ? (
          /* 大纲模式 - 结构版本 */
          <>
            <div className="flex-1 flex items-center justify-between px-8 py-4">
              <button
                onClick={() => setCurrentSlideIndex(Math.max(0, currentSlideIndex - 1))}
                disabled={currentSlideIndex === 0}
                className="bg-slate-200 hover:bg-slate-300 disabled:opacity-30 disabled:cursor-not-allowed text-slate-700 rounded-full p-4 transition shadow-lg z-10"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <div className="relative flex-1 mx-4 aspect-video shadow-xl animate-fade-in">
                <div className="absolute inset-0 rounded-2xl shadow-2xl overflow-hidden bg-gradient-to-br from-slate-600 to-slate-700 p-12">
                  {currentSlideIndex === 0 ? (
                    /* 封面 */
                    <div className="flex flex-col items-center justify-center h-full text-center">
                      <h1 className="text-6xl font-bold text-white mb-4">{topic}</h1>
                      <p className="text-xl text-slate-300">{stylePrompt}</p>
                    </div>
                  ) : (
                    /* 大纲页 */
                    <div className="flex flex-col h-full">
                      <h2 className="text-4xl font-bold text-white mb-8">
                        {outline[currentSlideIndex - 1]?.title || ''}
                      </h2>
                      <div className="space-y-3 flex-1">
                        {outline[currentSlideIndex - 1]?.bullets.map((bullet, i) => (
                          <div key={i} className="flex items-start gap-3">
                            <div className="w-2 h-2 rounded-full bg-white mt-2 flex-shrink-0"></div>
                            <p className="text-white text-xl">{bullet}</p>
                          </div>
                        ))}
                      </div>
                      <div className="text-slate-300 text-sm text-right">
                        {currentSlideIndex} / {outline.length}
                      </div>
                    </div>
                  )}
                </div>
              </div>
              <button
                onClick={() => setCurrentSlideIndex(Math.min(outline.length, currentSlideIndex + 1))}
                disabled={currentSlideIndex === outline.length}
                className="bg-slate-200 hover:bg-slate-300 disabled:opacity-30 disabled:cursor-not-allowed text-slate-700 rounded-full p-4 transition shadow-lg z-10"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>

            {/* 缩略图导航 */}
            <div className="border-t border-slate-300 bg-white p-4">
              <div className="flex gap-3 overflow-x-auto pb-2">
                {/* 封面缩略图 */}
                <button
                  onClick={() => setCurrentSlideIndex(0)}
                  className={`flex-shrink-0 w-48 aspect-video rounded-lg overflow-hidden border-2 transition p-3 bg-gradient-to-br from-slate-600 to-slate-700 ${currentSlideIndex === 0
                    ? "border-slate-400 ring-2 ring-slate-400/30"
                    : "border-slate-300 hover:border-slate-400"
                    }`}
                >
                  <div className="flex flex-col justify-center items-center h-full">
                    <p className="text-white text-xs font-semibold text-center line-clamp-2">{topic}</p>
                  </div>
                </button>

                {/* 大纲页缩略图 */}
                {outline.map((section, idx) => (
                  <button
                    key={idx}
                    onClick={() => setCurrentSlideIndex(idx + 1)}
                    className={`flex-shrink-0 w-48 aspect-video rounded-lg overflow-hidden border-2 transition p-3 bg-gradient-to-br from-slate-600 to-slate-700 ${currentSlideIndex === idx + 1
                      ? "border-slate-400 ring-2 ring-slate-400/30"
                      : "border-slate-300 hover:border-slate-400"
                      }`}
                  >
                    <div className="flex flex-col justify-between h-full">
                      <p className="text-white text-xs font-semibold line-clamp-2">{section.title}</p>
                      <p className="text-white text-xs opacity-50">{idx + 1}</p>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </>
        ) : (
          /* 空状态 */
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center space-y-4">
              <div className="text-6xl">📊</div>
              <h2 className="text-2xl font-semibold text-slate-600">准备开始</h2>
              <p className="text-slate-400">请在左侧输入主题并开始生成 PPT</p>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
