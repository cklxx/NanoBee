import { createEffect, createSignal, onCleanup } from "solid-js";

interface LogViewerProps {
  taskId: string;
  apiBase: string;
  initialLog?: string;
}

export function LogViewer(props: LogViewerProps) {
  const [log, setLog] = createSignal(props.initialLog ?? "");

  createEffect(() => {
    let source: EventSource | null = null;
    let pollHandle: ReturnType<typeof setInterval> | null = null;
    let retryHandle: ReturnType<typeof setTimeout> | null = null;
    let stopped = false;

    const fetchProgress = async () => {
      try {
        const res = await fetch(`${props.apiBase}/api/tasks/${props.taskId}/progress`);
        if (!res.ok) return;
        const data = await res.json();
        if (typeof data.progress === "string") {
          setLog(data.progress);
        }
      } catch (err) {
        console.error("Failed to poll progress", err);
      }
    };

    const startPolling = () => {
      if (pollHandle) return;
      fetchProgress();
      pollHandle = setInterval(fetchProgress, 3000);
    };

    const startStream = () => {
      if (source) return;
      source = new EventSource(`${props.apiBase}/api/tasks/${props.taskId}/progress/stream`);
      source.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          if (typeof parsed.progress === "string") {
            setLog(parsed.progress);
          }
        } catch (err) {
          console.error("Failed to parse progress update", err);
        }
      };
      source.onerror = (err) => {
        console.error("Progress stream error, falling back to polling", err);
        source?.close();
        source = null;
        if (!stopped) {
          startPolling();
          if (!retryHandle) {
            retryHandle = setTimeout(() => {
              retryHandle = null;
              if (!stopped) {
                startStream();
              }
            }, 10000);
          }
        }
      };
    };

    startStream();

    onCleanup(() => {
      stopped = true;
      source?.close();
      if (pollHandle) clearInterval(pollHandle);
      if (retryHandle) clearTimeout(retryHandle);
    });
  });

  return (
    <div class="card">
      <h3 class="text-lg font-semibold mb-2">Progress Log</h3>
      <pre class="bg-slate-50 border border-slate-200 rounded p-3 text-xs overflow-x-auto whitespace-pre-wrap">
        {log() || "No progress entries yet."}
      </pre>
    </div>
  );
}
