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
    const source = new EventSource(`${apiBase}/api/tasks/${taskId}/progress/stream`);

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
      console.error("Progress stream error", err);
    };

    return () => {
      source.close();
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
