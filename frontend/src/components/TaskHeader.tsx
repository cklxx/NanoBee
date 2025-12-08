import { createSignal, Show } from "solid-js";
import { Button } from "./ui/button";
import { runTaskAction } from "../lib/tasks";

const actionPath = {
  init: "/run/init",
  coding: "/run/coding/all",
  eval: "/evaluate",
} as const;

type ActionState = "init" | "coding" | "eval";

export function TaskHeader(props: {
  taskId: string;
  goal: string;
  status: string;
  workspace: string;
  onActionComplete?: () => void;
}) {
  const [pending, setPending] = createSignal<ActionState | null>(null);
  const [message, setMessage] = createSignal<string | null>(null);
  const [error, setError] = createSignal<string | null>(null);

  const trigger = async (action: ActionState) => {
    setPending(action);
    setError(null);
    setMessage(null);
    try {
      const result = await runTaskAction(props.taskId, action);
      setMessage(result.message);
      props.onActionComplete?.();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setPending(null);
    }
  };

  return (
    <div class="card space-y-2">
      <div class="flex items-start justify-between gap-4">
        <div>
          <p class="text-sm text-slate-600">Goal</p>
          <h2 class="text-xl font-semibold leading-tight">{props.goal}</h2>
          <p class="text-sm text-slate-600 mt-2">Workspace: {props.workspace}</p>
        </div>
        <div class="flex items-center gap-2">
          <span class="px-3 py-1 text-sm rounded-full bg-slate-100 border border-slate-200">{props.status}</span>
        </div>
      </div>
      <div class="flex flex-wrap gap-2">
        <Button onClick={() => trigger("init") } disabled={pending() === "init"}>
          {pending() === "init" ? "Working..." : "Run initializer"}
        </Button>
        <Button onClick={() => trigger("coding")} disabled={pending() === "coding"}>
          {pending() === "coding" ? "Working..." : "Run coding (all features)"}
        </Button>
        <Button onClick={() => trigger("eval")} disabled={pending() === "eval"}>
          {pending() === "eval" ? "Working..." : "Run evaluation"}
        </Button>
      </div>
      <Show when={message()}>
        {(msg) => <p class="text-sm text-green-700">{msg}</p>}
      </Show>
      <Show when={error()}>
        {(err) => <p class="text-sm text-red-700">{err}</p>}
      </Show>
    </div>
  );
}

