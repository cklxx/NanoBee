import { notFound } from "next/navigation";
import { FeatureTable } from "../../components/FeatureTable";
import { LogViewer } from "../../components/LogViewer";
import { TaskHeader } from "../../components/TaskHeader";
import { TaskTimeline, TimelineEvent } from "../../components/TaskTimeline";
import { WorkspaceFileTree } from "../../components/WorkspaceFileTree";
import { EvaluationPanel, EvalResult } from "../../components/EvaluationPanel";

const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${apiBase}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Request failed: ${path}`);
  }
  return res.json();
}

export default async function TaskDetail({ params }: { params: { id: string } }) {
  const taskId = params.id;

  let task: any;
  try {
    task = await fetchJSON(`/api/tasks/${taskId}`);
  } catch (err) {
    return notFound();
  }

  const [eventsRes, featuresRes, progressRes, filesRes, evalsRes] = await Promise.all([
    fetchJSON<{ events: TimelineEvent[] }>(`/api/tasks/${taskId}/events`),
    fetchJSON<{ features: any[] }>(`/api/tasks/${taskId}/features`),
    fetchJSON<{ progress: string }>(`/api/tasks/${taskId}/progress`),
    fetchJSON<{ files: string[] }>(`/api/workspaces/${task.workspace_id}/files`),
    fetchJSON<{ results: EvalResult[] }>(`/api/tasks/${taskId}/evals`).catch(() => ({ results: [] })),
  ]);

  return (
    <main className="space-y-4">
      <TaskHeader goal={task.goal} status={task.status} workspace={task.workspace_id} taskId={task.id} />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <TaskTimeline events={eventsRes.events} />
        <FeatureTable features={featuresRes.features} />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <LogViewer taskId={taskId} apiBase={apiBase} initialLog={progressRes.progress} />
        <WorkspaceFileTree files={filesRes.files} />
      </div>
      <EvaluationPanel results={evalsRes.results} />
    </main>
  );
}
