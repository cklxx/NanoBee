import { createSignal, onCleanup, Show } from "solid-js";

type LoadingTimerProps = {
    operation: "reference" | "outline" | "slides" | "images";
};

const OPERATION_LABELS = {
    reference: "搜索资料",
    outline: "生成大纲",
    slides: "生成内容",
    images: "生成图片",
} as const;

export function LoadingTimer(props: LoadingTimerProps) {
    const [elapsedSeconds, setElapsedSeconds] = createSignal(0);

    const interval = setInterval(() => {
        setElapsedSeconds((prev) => prev + 1);
    }, 1000);

    onCleanup(() => clearInterval(interval));

    return (
        <div class="bg-white rounded-lg border-2 border-blue-200 p-8 flex flex-col items-center gap-6 shadow-lg">
            {/* Spinning animation */}
            <div class="relative w-16 h-16">
                <div class="absolute inset-0 border-4 border-slate-200 rounded-full"></div>
                <div class="absolute inset-0 border-4 border-transparent border-t-blue-500 border-r-purple-500 rounded-full animate-spin"></div>
            </div>

            {/* Operation label */}
            <div class="text-center space-y-2">
                <h3 class="text-lg font-semibold text-slate-800">
                    {OPERATION_LABELS[props.operation]}中...
                </h3>
                <p class="text-sm text-slate-500">请稍候，AI正在努力工作</p>
            </div>

            {/* Timer */}
            <div class="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-50 to-purple-50 rounded-full">
                <svg
                    class="w-5 h-5 text-blue-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                >
                    <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                </svg>
                <span class="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                    {elapsedSeconds()}
                </span>
                <span class="text-sm text-slate-600">秒</span>
            </div>

            {/* Tip for long operations */}
            <Show when={elapsedSeconds() > 10}>
                <p class="text-xs text-slate-400 text-center max-w-xs">
                    操作时间较长，请耐心等待...
                </p>
            </Show>
        </div>
    );
}
