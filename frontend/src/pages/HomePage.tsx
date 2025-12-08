import { createResource, createSignal, For, Show } from "solid-js";
import { useNavigate, Link } from "@tanstack/solid-router";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { createTask, listTasks, TaskSummary } from "../lib/tasks";

const SAMPLE_GOALS = [
  "Build a FastAPI service that returns fibonacci numbers with caching",
  "Create a Solid dashboard with TanStack Router and shadcn components",
  "Write a CLI that syncs local markdown notes to a remote folder",
];

export function HomePage() {
  const navigate = useNavigate();
  const [goal, setGoal] = createSignal<string>(SAMPLE_GOALS[0]);
  const [notes, setNotes] = createSignal("Capture your ideas here and sync to your task goals.");
  const [pending, setPending] = createSignal(false);
  const [message, setMessage] = createSignal<string | null>(null);
  const [error, setError] = createSignal<string | null>(null);

  const [tasks, { refetch }] = createResource<TaskSummary[]>(listTasks);

  const goToTask = (id: string) => {
    navigate({ to: "/tasks/$id", params: { id } });
  };

  const submit = async (evt: Event) => {
    evt.preventDefault();
    setPending(true);
    setError(null);
    setMessage(null);
    try {
      const created = await createTask(goal());
      setMessage(`Created task ${created.id}`);
      setGoal("");
      await refetch();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setPending(false);
    }
  };

  return (
    <div class="grid gap-4 md:grid-cols-3">
      <div class="md:col-span-2 space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Create task</CardTitle>
            <CardDescription>Choose a preset goal or write your own to start a new workspace.</CardDescription>
          </CardHeader>
          <CardContent class="space-y-3">
            <form class="space-y-3" onSubmit={submit}>
              <label class="text-sm font-medium text-slate-700">Goal</label>
              <div class="space-y-2">
                <Input
                  list="sample-goals"
                  value={goal()}
                  onInput={(evt) => setGoal(evt.currentTarget.value)}
                  placeholder="Describe the task goal"
                />
                <datalist id="sample-goals">
                  <For each={SAMPLE_GOALS}>{(item) => <option value={item} />}</For>
                </datalist>
                <div class="flex flex-wrap gap-2">
                  <For each={SAMPLE_GOALS}>
                    {(item) => (
                      <button
                        type="button"
                        onClick={() => setGoal(item)}
                        class="text-xs px-3 py-2 rounded-md border border-slate-200 bg-slate-50 hover:bg-slate-100"
                      >
                        {item}
                      </button>
                    )}
                  </For>
                </div>
              </div>
              <div class="space-y-1">
                <label class="text-sm font-medium text-slate-700">Notes</label>
                <Textarea
                  rows={3}
                  value={notes()}
                  onInput={(evt) => setNotes(evt.currentTarget.value)}
                  placeholder="Optional context stored locally for your reference"
                />
              </div>
              <div class="flex items-center justify-between">
                <div class="space-y-0.5 text-xs text-slate-600">
                  <p>Tasks are stored locally for the demo and can be opened for more details.</p>
                  <p>Notes stay in your browser and are not sent to the backend.</p>
                </div>
                <Button type="submit" disabled={pending()}>
                  {pending() ? "Creating..." : "Create"}
                </Button>
              </div>
            </form>
            <Show when={message()}>
              {(msg) => <p class="text-sm text-green-700">{msg()}</p>}
            </Show>
            <Show when={error()}>
              {(err) => <p class="text-sm text-red-700">{err()}</p>}
            </Show>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Tasks</CardTitle>
            <CardDescription>Your recent workspaces</CardDescription>
          </CardHeader>
          <CardContent>
            <Show when={tasks()} fallback={<p class="text-sm text-slate-600">Loading tasks...</p>}>
              {(list) => (
                <Show when={list().length} fallback={<p class="text-sm text-slate-600">No tasks yet.</p>}>
                  <div class="grid grid-cols-1 gap-3">
                    <For each={list()}>
                      {(task) => (
                        <button
                          class="card text-left hover:border-blue-200"
                          onClick={() => goToTask(task.id)}
                        >
                          <div class="flex items-center justify-between">
                            <div>
                              <h3 class="text-lg font-semibold">{task.goal}</h3>
                              <p class="text-sm text-slate-600">Task ID: {task.id}</p>
                              <p class="text-sm text-slate-600">Workspace: {task.workspace_id}</p>
                            </div>
                            <span class="px-3 py-1 text-sm rounded-full bg-slate-100 border border-slate-200">
                              {task.status}
                            </span>
                          </div>
                        </button>
                      )}
                    </For>
                  </div>
                </Show>
              )}
            </Show>
          </CardContent>
        </Card>
      </div>
      <div class="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Quick links</CardTitle>
            <CardDescription>Common entry points</CardDescription>
          </CardHeader>
          <CardContent class="space-y-2 text-sm text-slate-700">
            <div class="flex items-center justify-between">
              <span>API Key 获取</span>
              <Link to="/guide/volcengine" class="underline">查看</Link>
            </div>
            <div class="flex items-center justify-between">
              <span>Latest task</span>
              <Show when={tasks()?.[0]} fallback={<span class="text-slate-500">暂无</span>}>
                {(task) => (
                  <button class="underline" onClick={() => goToTask(task().id)}>
                    {task().id}
                  </button>
                )}
              </Show>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
