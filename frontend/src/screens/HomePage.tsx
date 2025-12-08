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
      const response = await fetch(`${apiBase}/api/ppt/outline`, {
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
        let errorDetail = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const errorJson = JSON.parse(errorText);
          errorDetail = errorJson.detail || errorJson.message || errorText;
        } catch {
          errorDetail = errorText || errorDetail;
        }
        throw new Error(`大纲生成失败 - ${errorDetail}`);
      }
      const data = await response.json();
      setOutline(data.outline || []);
      pushStatus(`✓ 大纲生成完成，共 ${data.outline?.length || 0} 个部分`);
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

  return (
    <div class="min-h-screen bg-slate-50">
      <div class="border-b bg-white">
        <div class="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between gap-4">
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

      <div class="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6 px-4 py-6">
        <div class="space-y-4">
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

        <div class="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle class="text-lg">生成预览</CardTitle>
              <CardDescription>大纲、内容与图片预览</CardDescription>
            </CardHeader>
            <CardContent class="space-y-4">
              <Show
                when={currentSlide()}
                fallback={
                  <Show
                    when={busy()}
                    fallback={<p class="text-slate-500">请先生成大纲或内容</p>}
                  >
                    <LoadingTimer operation={busy() as "reference" | "outline" | "slides" | "images"} />
                  </Show>
                }
              >
                <div class="flex flex-col gap-4">
                  <div class="flex items-start gap-4">
                    <div class="flex-1 space-y-3">
                      <p class="text-sm uppercase tracking-wide text-slate-500">{currentSlide()?.title}</p>
                      <div class="space-y-2">
                        <For each={currentSlide()?.bullets || []}>
                          {(bullet) => <p class="text-slate-800">• {bullet}</p>}
                        </For>
                      </div>
                    </div>
                    <div class="w-64 h-40 border rounded-lg bg-slate-100 flex items-center justify-center overflow-hidden">
                      <Show when={currentImage()?.url || currentImage()?.data_url} fallback={<span class="text-slate-400">等待图片</span>}>
                        <img
                          src={currentImage()?.url || currentImage()?.data_url}
                          alt={currentSlide()?.title || "slide"}
                          class="w-full h-full object-cover"
                        />
                      </Show>
                    </div>
                  </div>
                  <div class="flex gap-2 overflow-x-auto pb-2">
                    <For each={slides()}>
                      {(slide, idx) => (
                        <button
                          class={`px-3 py-2 rounded border ${idx() === currentSlideIndex() ? "border-slate-500 bg-slate-100" : "border-slate-200"}`}
                          onClick={() => setCurrentSlideIndex(idx())}
                        >
                          <p class="text-sm font-medium truncate w-48 text-left">{slide.title}</p>
                          <p class="text-xs text-slate-500">{idx() + 1}/{slides().length}</p>
                        </button>
                      )}
                    </For>
                  </div>
                </div>
              </Show>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle class="text-lg">参考资料</CardTitle>
              <CardDescription>搜索结果（最多 6 条）</CardDescription>
            </CardHeader>
            <CardContent class="space-y-3">
              <For each={references()}>
                {(ref) => (
                  <div class="p-3 border rounded-lg space-y-1">
                    <p class="font-medium">{ref.title}</p>
                    <p class="text-sm text-slate-600">{ref.summary}</p>
                    <a class="text-sm" href={ref.url} target="_blank" rel="noreferrer">
                      {ref.source}
                    </a>
                  </div>
                )}
              </For>
              <Show when={!references().length}>
                <p class="text-sm text-slate-400">等待生成</p>
              </Show>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
