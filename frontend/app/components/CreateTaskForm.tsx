"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

const SAMPLE_GOALS = [
  "Build a FastAPI service that returns fibonacci numbers with caching",
  "Create a Next.js todo app with Tailwind styling and persistent storage",
  "Write a CLI that syncs local markdown notes to a remote folder",
];

export function CreateTaskForm() {
  const router = useRouter();
  const [goal, setGoal] = useState<string>(SAMPLE_GOALS[0]);
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!goal.trim()) {
      setError("Goal is required");
      return;
    }
    setPending(true);
    setMessage(null);
    setError(null);
    try {
      const res = await fetch(`${apiBase}/api/tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ goal: goal.trim() }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = typeof data.detail === "string" ? data.detail : "Failed to create task";
        throw new Error(detail);
      }
      setMessage(`Created task ${data.id}`);
      setGoal("");
      router.refresh();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setPending(false);
    }
  };

  return (
    <form onSubmit={submit} className="card space-y-3">
      <div className="flex items-center justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold">Create task</h2>
          <p className="text-sm text-slate-600">Choose a preset goal or write your own to start a new workspace.</p>
        </div>
        <button
          type="submit"
          disabled={pending}
          className="px-4 py-2 rounded-md bg-blue-600 text-white text-sm disabled:opacity-60"
        >
          {pending ? "Creating..." : "Create"}
        </button>
      </div>
      <div className="space-y-2">
        <input
          list="sample-goals"
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          placeholder="Describe the task goal"
          className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
        />
        <datalist id="sample-goals">
          {SAMPLE_GOALS.map((item) => (
            <option key={item} value={item} />
          ))}
        </datalist>
        <div className="flex flex-wrap gap-2">
          {SAMPLE_GOALS.map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => setGoal(item)}
              className="text-xs px-3 py-2 rounded-md border border-slate-200 bg-slate-50 hover:bg-slate-100"
            >
              {item}
            </button>
          ))}
        </div>
      </div>
      {message ? <p className="text-sm text-green-700">{message}</p> : null}
      {error ? <p className="text-sm text-red-700">{error}</p> : null}
    </form>
  );
}
