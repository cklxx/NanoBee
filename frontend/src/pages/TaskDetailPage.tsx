import { createResource, Show } from "solid-js";
import { useParams } from "@tanstack/solid-router";
import { apiBase } from "../lib/api";
import { TaskHeader } from "../components/TaskHeader";
import { TaskTimeline } from "../components/TaskTimeline";
import { FeatureTable } from "../components/FeatureTable";
import { LogViewer } from "../components/LogViewer";
import { WorkspaceFileTree } from "../components/WorkspaceFileTree";
import { EvaluationPanel } from "../components/EvaluationPanel";
import { getTaskDetail } from "../lib/tasks";

export function TaskDetailPage() {
  const params = useParams({ from: "/tasks/$id" });

  const [taskData, { refetch }] = createResource(params.id, getTaskDetail);

  return (
    <div class="space-y-4">
      <Show when={taskData.error}>
        {(err) => <div class="card text-sm text-red-700">加载任务失败: {(err as Error).message}</div>}
      </Show>
      <Show when={taskData.state === "pending"}>
        <div class="card text-sm">正在加载任务数据...</div>
      </Show>
      <Show when={taskData()}>
        {(data) => (
          <>
            <TaskHeader
              taskId={data().task.id}
              goal={data().task.goal}
              status={data().task.status}
              workspace={data().task.workspace_id}
              onActionComplete={() => refetch()}
            />
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <TaskTimeline events={data().events} />
              <FeatureTable features={data().features} />
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <LogViewer taskId={params.id} apiBase={apiBase} initialLog={data().progress} />
              <WorkspaceFileTree files={data().files} />
            </div>
            <EvaluationPanel results={data().evals} />
          </>
        )}
      </Show>
    </div>
  );
}
