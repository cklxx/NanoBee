import { createEffect, createMemo, createSignal, For, Show } from "solid-js";
import jsPDF from "jspdf";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { LoadingTimer } from "@/components/LoadingTimer";

const apiBase = import.meta.env.VITE_API_BASE || "http://localhost:8000";

type ReferenceArticle = {
  title: string;
  url: string;
  summary: string;
  source: string;
  rank?: number;
};

type OutlineSection = {
  title: string;
  bullets: string[];
};

type SlideContent = {
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
};

type SlideImage = {
  title: string;
  style_seed: string;
  model: string;
  base_url?: string;
  watermark?: boolean;
  url?: string;
  data_url?: string;
};

export function HomePage() {
  const [topic, setTopic] = createSignal("人工智能发展历史");
  const [stylePrompt, setStylePrompt] = createSignal("简洁商务 · 大胆配色 · 几何元素");
  const [references, setReferences] = createSignal<ReferenceArticle[]>([]);
  const [outline, setOutline] = createSignal<OutlineSection[]>([]);
  const [slides, setSlides] = createSignal<SlideContent[]>([]);
  const [slideImages, setSlideImages] = createSignal<SlideImage[]>([]);
  const [statusLog, setStatusLog] = createSignal<string[]>([]);
  const [busy, setBusy] = createSignal<string | null>(null);
  const [currentSlideIndex, setCurrentSlideIndex] = createSignal(0);
  const [apiKey, setApiKey] = createSignal("");
  const [sessionId, setSessionId] = createSignal<string | null>(null);

  createEffect(() => {
    const key = localStorage.getItem("nanobee_api_key");
    if (key) setApiKey(key);
    const savedSession = localStorage.getItem("nanobee_session");
    const initialSession = savedSession || crypto.randomUUID();
    setSessionId(initialSession);
    localStorage.setItem("nanobee_session", initialSession);
  });

  const pushStatus = (message: string) =>
    setStatusLog((prev) => [`${new Date().toLocaleTimeString()} · ${message}`, ...prev].slice(0, 30));

  const resetSession = () => {
    const next = crypto.randomUUID();
    setSessionId(next);
    localStorage.setItem("nanobee_session", next);
    pushStatus(`✓ 已切换到新的会话 (${next.slice(0, 8)})`);
  };

  const handleApiKeyChange = (value: string) => {
    setApiKey(value);
    localStorage.setItem("nanobee_api_key", value);
  };

  const runReferenceSearch = async () => {
    setBusy("reference");
    pushStatus(`正在搜索关于 "${topic()}" 的参考资料...`);
    try {
      const response = await fetch(`${apiBase}/api/ppt/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic: topic(), limit: 6, session_id: sessionId() }),
      });
      if (!response.ok) {
        const errorText = await response.text();
        let errorDetail = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const errorJson = JSON.parse(errorText);
          errorDetail = errorJson.detail || errorJson.message || errorText;
        } catch {
          errorDetail = errorText || errorDetail;
        }
        throw new Error(`搜索失败 - ${errorDetail}`);
      }
      const data = await response.json();
      setReferences(data.references || []);
      pushStatus(`✓ 找到 ${data.references?.length || 0} 个参考资料`);
    } catch (error: any) {
      const fullError = `✗ 搜索失败: ${error.message}`;
      pushStatus(fullError);
      console.error("Reference search error:", error);
    } finally {
      setBusy(null);
    }
  };

  const runOutline = async () => {
    if (!references().length) await runReferenceSearch();
    setBusy("outline");
    pushStatus(`正在生成 PPT 大纲...`);

    try {
      const response = await fetch(`${apiBase}/api/ppt/outline-stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic: topic(),
          references: references(),
          session_id: sessionId(),
          text_model: apiKey()
            ? { model: "doubao-seed-1-6-251015", base_url: "", api_key: apiKey() }
            : undefined,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`大纲生成失败 - HTTP ${response.status}: ${errorText}`);
      }

      // Read SSE stream
      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("无法读取响应流");
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || ""; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));

              switch (data.type) {
                case "progress":
                  pushStatus(`🔄 第${data.round}/3轮：${data.message}`);
                  break;

                case "partial":
                  // Progressively update outline
                  setOutline((prev) => [...prev, ...data.sections]);
                  pushStatus(`✓ ${data.message}`);
                  break;

                case "partial_complete":
                  // Handle partial completion (some rounds failed)
                  setOutline(data.outline || []);
                  pushStatus(`⚠ ${data.message}`);
                  break;

                case "complete":
                  setOutline(data.outline || []);
                  pushStatus(`✓ ${data.message}`);
                  break;

                case "error":
                  pushStatus(`✗ 大纲生成失败: ${data.error}`);
                  console.error("Outline generation error:", data.error);
                  break;
              }
            } catch (e) {
              console.error("Failed to parse SSE data:", line, e);
            }
          }
        }
      }
    } catch (error: any) {
      const fullError = `✗ 大纲生成失败: ${error.message}`;
      pushStatus(fullError);
      console.error("Outline generation error:", error);
    } finally {
      setBusy(null);
    }
  };

  const runSlides = async (): Promise<SlideContent[]> => {
    if (!outline().length) await runOutline();
    setBusy("slides");
    pushStatus(`正在生成每页PPT内容...`);
    try {
      const response = await fetch(`${apiBase}/api/ppt/slides`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic: topic(),
          outline: outline(),
          references: references(),
          style_prompt: stylePrompt(),
          session_id: sessionId(),
          text_model: apiKey()
            ? { model: "doubao-seed-1-6-251015", base_url: "", api_key: apiKey() }
            : undefined,
        }),
      });
      if (!response.ok) {
        const errorText = await response.text();
        let errorDetail = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const errorJson = JSON.parse(errorText);
          errorDetail = errorJson.detail || errorJson.message || errorText;
        } catch {
          errorDetail = errorText || errorDetail;
        }
        throw new Error(`幻灯片生成失败 - ${errorDetail}`);
      }
      const data = await response.json();
      setSlides(data.slides || []);
      pushStatus(`✓ 生成了 ${data.slides?.length || 0} 页幻灯片`);
      return data.slides || [];
    } catch (error: any) {
      const fullError = `✗ 幻灯片生成失败: ${error.message}`;
      pushStatus(fullError);
      console.error("Slides generation error:", error);
      return [];
    } finally {
      setBusy(null);
    }
  };

  const runImages = async () => {
    const slidesToUse = slides().length ? slides() : await runSlides();
    if (!slidesToUse.length) {
      pushStatus("✗ 没有可生成图片的幻灯片");
      return;
    }
    setBusy("images");
    pushStatus(`调用 SeaDream 生成 PPT 页面，这可能需要一些时间...`);

    const upsertImage = (img: SlideImage) => {
      setSlideImages((prev) => {
        const next = [...prev];
        const idx = next.findIndex((i) => i.title === img.title);
        if (idx >= 0) next[idx] = { ...next[idx], ...img };
        else next.push(img);
        return next;
      });
    };

    const generateImageForSlide = async (slide: SlideContent): Promise<SlideImage | null> => {
      const body = {
        topic: topic(),
        slides: [slide],
        watermark: false,
        session_id: sessionId(),
        image_model: apiKey() ? { model: "doubao-seedream-4-5-251128", base_url: "", api_key: apiKey() } : undefined,
      };
      try {
        const response = await fetch(`${apiBase}/api/ppt/images`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        if (!response.ok) throw new Error(response.statusText);
        const data = await response.json();
        const image: SlideImage | undefined = data.images?.[0];
        return image || null;
      } catch (err: any) {
        pushStatus(`✗ 图片生成失败（${slide.title}）：${err.message || err}`);
        return null;
      }
    };

    try {
      if (slidesToUse.length > 0) {
        const firstImage = await generateImageForSlide(slidesToUse[0]);
        if (firstImage) {
          upsertImage(firstImage);
          pushStatus(`✓ 首张图片完成：${slidesToUse[0].title}`);
        }
      }

      const remaining = slidesToUse.slice(1);
      if (remaining.length) {
        const results = await Promise.allSettled(remaining.map(generateImageForSlide));
        results.forEach((res, idx) => {
          if (res.status === "fulfilled" && res.value) {
            upsertImage(res.value);
          } else if (res.status === "rejected") {
            pushStatus(`✗ 图片生成失败（${remaining[idx].title}）：${res.reason}`);
          }
        });
        pushStatus(`✓ 已生成 ${results.filter((r) => r.status === "fulfilled").length}/${remaining.length} 张图片`);
      }
    } catch (error: any) {
      pushStatus(`✗ PPT 页面生成失败: ${error.message}`);
    } finally {
      setBusy(null);
    }
  };

  const fetchImageDataUrl = async (image: SlideImage): Promise<string | null> => {
    if (image.data_url) return image.data_url;
    if (!image.url) return null;
    try {
      const res = await fetch(image.url);
      if (!res.ok) return null;
      const blob = await res.blob();
      return await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result as string);
        reader.onerror = () => reject(reader.error);
        reader.readAsDataURL(blob);
      });
    } catch (err) {
      console.error("Failed to fetch image data URL", err);
      return null;
    }
  };

  const downloadPdf = async () => {
    if (!slides().length) return;
    const doc = new jsPDF({ orientation: "landscape", unit: "pt", format: "a4" });
    for (let idx = 0; idx < slides().length; idx++) {
      const slide = slides()[idx];
      if (idx !== 0) doc.addPage();
      doc.setFontSize(24);
      doc.text(slide.title, 60, 80);
      doc.setFontSize(14);
      slide.bullets.forEach((b, i) => doc.text(`• ${b}`, 80, 130 + i * 24));
      const image = slideImages().find((img) => img.title === slide.title);
      if (image) {
        const dataUrl = await fetchImageDataUrl(image);
        if (dataUrl) {
          try {
            doc.addImage(dataUrl, "PNG", 400, 90, 320, 180);
          } catch (e) {
            console.error("Failed to add image to PDF", e);
          }
        }
      }
    }
    doc.save(`${topic()}.pdf`);
    pushStatus("✓ PDF 已导出");
  };

  const currentSlide = createMemo(() => slides()[currentSlideIndex()]);
  const currentImage = createMemo(() => slideImages().find((img) => img.title === currentSlide()?.title));

  // Convert outline to slide format for unified preview
  const outlineAsSlides = createMemo(() =>
    outline().map(section => ({
      title: section.title,
      bullets: section.bullets,
      keywords: "", // Outline doesn't have keywords yet
    }))
  );

  // Use slides if available, otherwise use outline as slides
  const previewSlides = createMemo(() => slides().length > 0 ? slides() : outlineAsSlides());
  const currentPreviewSlide = createMemo(() => previewSlides()[currentSlideIndex()]);


  return (
    <div class="min-h-screen bg-slate-50">
      <div class="border-b bg-white">
        <div class="border-b bg-white">
          <div class="w-full px-6 py-4 flex items-center justify-between gap-4">
            <div>
              <p class="text-xs uppercase tracking-wide text-slate-500">TanStack Router + Solid</p>
              <h1 class="text-3xl font-bold text-slate-800">NanoBee PPT</h1>
              <p class="text-slate-500">AI 驱动的 PPT 生成工作流</p>
            </div>
            <div class="flex items-center gap-2">
              <Badge variant="secondary" class="text-xs">
                Session {sessionId()?.slice(0, 8)}
              </Badge>
              <Button variant="outline" size="sm" onClick={resetSession}>
                新会话
              </Button>
            </div>
          </div>
        </div>

        <div class="w-full grid grid-cols-1 lg:grid-cols-12 gap-6 px-6 py-6">
          <div class="space-y-4 lg:col-span-4 xl:col-span-3">
            <Show
              when={references().length > 0}
              fallback={
                <Card>
                  <CardHeader>
                    <CardTitle class="text-lg">1. 主题与风格</CardTitle>
                    <CardDescription>设置 PPT 主题与风格提示词</CardDescription>
                  </CardHeader>
                  <CardContent class="space-y-4">
                    <div class="space-y-2">
                      <Label for="topic">PPT 主题</Label>
                      <Input
                        id="topic"
                        value={topic()}
                        onInput={(e) => setTopic(e.currentTarget.value)}
                        placeholder="例如：人工智能发展历史"
                      />
                    </div>
                    <div class="space-y-2">
                      <Label for="style">风格描述</Label>
                      <Textarea
                        id="style"
                        rows={2}
                        value={stylePrompt()}
                        onInput={(e) => setStylePrompt(e.currentTarget.value)}
                        placeholder="例如：极简 · 柔和渐变 · 科技感"
                      />
                    </div>
                  </CardContent>
                </Card>
              }
            >
              <Card>
                <CardHeader>
                  <div class="flex items-center justify-between">
                    <div>
                      <CardTitle class="text-lg">参考资料</CardTitle>
                      <CardDescription>已基于主题搜索到 {references().length} 条资料</CardDescription>
                    </div>
                    <Button variant="ghost" size="sm" class="text-xs h-7" onClick={() => setReferences([])}>
                      ✏️ 修改主题
                    </Button>
                  </div>
                </CardHeader>
                <CardContent class="space-y-3 max-h-[400px] overflow-y-auto">
                  <For each={references()}>
                    {(ref) => (
                      <div class="p-3 border rounded-lg space-y-1 bg-white">
                        <p class="font-medium text-sm">{ref.title}</p>
                        <p class="text-xs text-slate-500 line-clamp-2">{ref.summary}</p>
                        <a class="text-xs text-blue-500 hover:underline" href={ref.url} target="_blank" rel="noreferrer">
                          {ref.source}
                        </a>
                      </div>
                    )}
                  </For>
                </CardContent>
              </Card>
            </Show>

            <Card>
              <CardHeader>
                <CardTitle class="text-lg">2. 模型配置</CardTitle>
                <CardDescription>可选：自定义火山引擎 API Key</CardDescription>
              </CardHeader>
              <CardContent class="space-y-3">
                <Input
                  placeholder="sk-..."
                  value={apiKey()}
                  onInput={(e) => handleApiKeyChange(e.currentTarget.value)}
                />
                <p class="text-xs text-slate-500">
                  密钥仅保存在浏览器本地，用于覆盖默认接入点。
                </p>
                <div class="flex gap-2">
                  <Button class="flex-1" onClick={runReferenceSearch} disabled={!!busy()}>
                    📚 搜索资料
                  </Button>
                  <Button class="flex-1" onClick={runOutline} disabled={!!busy()}>
                    🧭 生成大纲
                  </Button>
                </div>
                <div class="flex gap-2">
                  <Button class="flex-1" onClick={runSlides} disabled={!!busy()}>
                    📝 生成内容
                  </Button>
                  <Button class="flex-1" onClick={runImages} disabled={!!busy()}>
                    🖼️ 生成图片
                  </Button>
                </div>
                <Button variant="outline" class="w-full" onClick={downloadPdf} disabled={!slides().length}>
                  ⬇️ 导出 PDF
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle class="text-lg">最近状态</CardTitle>
                <CardDescription>跟踪每一步的执行结果</CardDescription>
              </CardHeader>
              <CardContent>
                <div class="space-y-1 text-sm text-slate-600 max-h-48 overflow-y-auto">
                  <For each={statusLog()}>{(item) => <p>{item}</p>}</For>
                  <Show when={!statusLog().length}>
                    <p class="text-slate-400">暂无记录</p>
                  </Show>
                </div>
              </CardContent>
            </Card>
          </div>

          <div class="lg:col-span-8 xl:col-span-9 space-y-4">
            <Card>
              <CardHeader>
                <CardTitle class="text-lg">生成预览</CardTitle>
                <CardDescription>大纲、内容与图片预览</CardDescription>
              </CardHeader>
              <CardContent class="space-y-4">
                <Show
                  when={currentPreviewSlide()}
                  fallback={
                    <Show
                      when={busy()}
                      fallback={
                        <div class="aspect-video bg-slate-100 rounded-lg flex flex-col items-center justify-center p-8 text-center">
                          <p class="text-slate-500 mb-2">👋 欢迎使用 NanoBee PPT</p>
                          <p class="text-sm text-slate-400">在左侧配置主题，即可开始生成</p>
                        </div>
                      }
                    >
                      <div class="aspect-video bg-slate-50 rounded-lg flex flex-col items-center justify-center relative overflow-hidden">
                        <LoadingTimer operation={busy() as "reference" | "outline" | "slides" | "images"} />
                      </div>
                    </Show>
                  }
                >
                  <div class="flex flex-col gap-4">
                    {/* 16:9 Slide Preview Container */}
                    <div class="aspect-video bg-white border shadow-sm rounded-lg relative overflow-hidden flex flex-col">
                      {/* Background Image Layer */}
                      <Show when={currentImage()?.url || currentImage()?.data_url}>
                        <div class="absolute inset-0 z-0">
                          <img
                            src={currentImage()?.url || currentImage()?.data_url}
                            alt={currentPreviewSlide()?.title || "slide"}
                            class="w-full h-full object-cover opacity-20"
                          />
                          <div class="absolute inset-0 bg-gradient-to-t from-white/90 to-white/60" />
                        </div>
                      </Show>

                      {/* Content Layer */}
                      <div class="relative z-10 flex-1 p-8 sm:p-12 md:p-16 flex flex-col justify-center">
                        <h2 class="text-3xl sm:text-4xl font-bold text-slate-900 mb-6 sm:mb-8 leading-tight">
                          {currentPreviewSlide()?.title}
                        </h2>
                        <div class="space-y-4 sm:space-y-6">
                          <For each={currentPreviewSlide()?.bullets || []}>
                            {(bullet) => (
                              <div class="flex items-start gap-4">
                                <span class="w-2 h-2 rounded-full bg-blue-600 mt-2.5 flex-shrink-0" />
                                <p class="text-lg sm:text-xl text-slate-800 leading-relaxed">{bullet}</p>
                              </div>
                            )}
                          </For>
                        </div>
                      </div>

                      {/* Footer */}
                      <div class="relative z-10 px-8 py-4 flex justify-between items-center text-xs text-slate-400 border-t border-slate-100/50">
                        <span>NanoBee AI Generated</span>
                        <span>{currentSlideIndex() + 1} / {previewSlides().length}</span>
                      </div>
                    </div>

                    {/* Slide navigation */}
                    <div class="flex gap-2 overflow-x-auto pb-2 min-h-[80px]">
                      <For each={previewSlides()}>
                        {(slide, idx) => (
                          <button
                            class={`flex-shrink-0 w-32 aspect-video rounded border flex flex-col p-2 text-left transition-all ${idx() === currentSlideIndex()
                              ? "border-blue-500 ring-2 ring-blue-100 bg-white"
                              : "border-slate-200 hover:border-slate-300 bg-slate-50"
                              }`}
                            onClick={() => setCurrentSlideIndex(idx())}
                          >
                            <div class="flex-1 overflow-hidden">
                              <p class="text-[10px] font-bold text-slate-700 leading-tight line-clamp-2">{slide.title}</p>
                            </div>
                            <p class="text-[10px] text-slate-400 mt-1">{idx() + 1}</p>
                          </button>
                        )}
                      </For>
                    </div>

                    {/* Show hint when viewing outline */}
                    <Show when={slides().length === 0 && outline().length > 0}>
                      <div class="flex items-center justify-center gap-2 p-2 bg-blue-50 text-blue-700 text-sm rounded border border-blue-100">
                        <span>ℹ️ 当前为大纲预览模式</span>
                        <span class="text-blue-400">|</span>
                        <span>点击"生成内容"继续完善</span>
                      </div>
                    </Show>
                  </div>
                </Show>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
