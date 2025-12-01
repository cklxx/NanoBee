"use client";

import { useEffect, useState } from "react";

interface LogViewerProps {
  taskId: string;
  apiBase: string;
  initialLog?: string;
}

export function LogViewer({ taskId, apiBase, initialLog = "" }: LogViewerProps) {
  const [log, setLog] = useState(initialLog);

  useEffect(() => {
    let source: EventSource | null = null;
    let pollHandle: ReturnType<typeof setInterval> | null = null;
    let retryHandle: ReturnType<typeof setTimeout> | null = null;
    let stopped = false;

    const fetchProgress = async () => {
      try {
        const res = await fetch(`${apiBase}/api/tasks/${taskId}/progress`);
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
      // Keep the UI updating even if streaming fails.
      fetchProgress();
      pollHandle = setInterval(fetchProgress, 3000);
    };

    const startStream = () => {
      if (source) return;

      source = new EventSource(`${apiBase}/api/tasks/${taskId}/progress/stream`);

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

    return () => {
      stopped = true;
      source?.close();
      if (pollHandle) {
        clearInterval(pollHandle);
      }
      if (retryHandle) {
        clearTimeout(retryHandle);
      }
    };
  }, [apiBase, taskId]);

  return (
    <div className="card">
      <h3 className="text-lg font-semibold mb-2">Progress Log</h3>
      <pre className="bg-slate-50 border border-slate-200 rounded p-3 text-xs overflow-x-auto whitespace-pre-wrap">
        {log || "No progress entries yet."}
      </pre>
    </div>
  );
}
