"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

type ActionState = {
  label: string;
  action: "init" | "coding" | "eval";
};

type Props = {
  taskId: string;
  goal: string;
  status: string;
  workspace: string;
};

async function postJson(path: string): Promise<any> {
  const res = await fetch(path, { method: "POST" });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = typeof data.detail === "string" ? data.detail : "Request failed";
    throw new Error(detail);
  }
  return data;
}

export function TaskHeader({ taskId, goal, status, workspace }: Props) {
  const router = useRouter();
  const [pending, setPending] = useState<ActionState | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const trigger = async (action: ActionState) => {
    setPending(action);
    setError(null);
    setMessage(null);
    try {
      const payload = await postJson(`${apiBase}/api/tasks/${taskId}${actionPath(action.action)}`);
      const summary = summarizeResult(action.action, payload);
      setMessage(summary);
      router.refresh();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setPending(null);
    }
  };

  return (
    <div className="card space-y-2">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-slate-600">Goal</p>
          <h2 className="text-xl font-semibold leading-tight">{goal}</h2>
          <p className="text-sm text-slate-600 mt-2">Workspace: {workspace}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-3 py-1 text-sm rounded-full bg-slate-100 border border-slate-200">{status}</span>
        </div>
      </div>
      <div className="flex flex-wrap gap-2">
        <ActionButton
          label="Run initializer"
          onClick={() => trigger({ label: "initializer", action: "init" })}
          pending={pending?.action === "init"}
        />
        <ActionButton
          label="Run coding (all features)"
          onClick={() => trigger({ label: "coding", action: "coding" })}
          pending={pending?.action === "coding"}
        />
        <ActionButton
          label="Run evaluation"
          onClick={() => trigger({ label: "evaluation", action: "eval" })}
          pending={pending?.action === "eval"}
        />
      </div>
      {message ? <p className="text-sm text-green-700">{message}</p> : null}
      {error ? <p className="text-sm text-red-700">{error}</p> : null}
    </div>
  );
}

function ActionButton({
  label,
  onClick,
  pending,
}: {
  label: string;
  onClick: () => void;
  pending: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={pending}
      className="px-3 py-2 rounded-md bg-slate-900 text-white text-sm disabled:opacity-60"
    >
      {pending ? "Working..." : label}
    </button>
  );
}

function actionPath(action: ActionState["action"]): string {
  if (action === "init") return "/run/init";
  if (action === "coding") return "/run/coding/all";
  return "/evaluate";
}

function summarizeResult(action: ActionState["action"], payload: any): string {
  if (action === "init") {
    const count = Array.isArray(payload.files) ? payload.files.length : 0;
    return `Initializer finished (${count} files written)`;
  }
  if (action === "coding") {
    const sessions = Array.isArray(payload.sessions) ? payload.sessions.length : 0;
    const remaining = Array.isArray(payload.remaining) ? payload.remaining.length : 0;
    return `Coding sessions: ${sessions}, remaining failing features: ${remaining}`;
  }
  const score = typeof payload.score === "number" ? payload.score : "n/a";
  return `Evaluation completed (score: ${score})`;
}
