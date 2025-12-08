import { Feature } from "../components/FeatureTable";
import { EvalResult } from "../components/EvaluationPanel";
import { TimelineEvent } from "../components/TaskTimeline";

export type TaskSummary = {
  id: string;
  goal: string;
  status: string;
  workspace_id: string;
  created_at: string;
};

export type TaskDetail = {
  task: TaskSummary;
  events: TimelineEvent[];
  features: Feature[];
  progress: string;
  files: string[];
  evals: EvalResult[];
};

const STORAGE_KEY = "nanobee_tasks";

function loadTasks(): TaskSummary[] {
  if (typeof window === "undefined") return seedTasks();
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) return seedAndPersist();
  try {
    const parsed = JSON.parse(raw) as TaskSummary[];
    return parsed.length ? parsed : seedAndPersist();
  } catch (err) {
    console.warn("Failed to parse stored tasks, seeding new list", err);
    return seedAndPersist();
  }
}

function persistTasks(tasks: TaskSummary[]) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks));
}

function seedTasks(): TaskSummary[] {
  const now = new Date().toISOString();
  return [
    {
      id: "task-demo",
      goal: "Draft a developer pitch deck for NanoBee platform",
      status: "pending",
      workspace_id: "ws-demo",
      created_at: now,
    },
    {
      id: "task-solid-upgrade",
      goal: "Upgrade frontend to Solid + TanStack Router",
      status: "completed",
      workspace_id: "ws-solid",
      created_at: now,
    },
  ];
}

function seedAndPersist() {
  const seeded = seedTasks();
  persistTasks(seeded);
  return seeded;
}

export async function listTasks(): Promise<TaskSummary[]> {
  return loadTasks();
}

export async function createTask(goal: string): Promise<TaskSummary> {
  const trimmed = goal.trim();
  if (!trimmed) {
    throw new Error("Goal is required");
  }
  const now = new Date();
  const newTask: TaskSummary = {
    id: `task-${now.getTime()}`,
    goal: trimmed,
    status: "pending",
    workspace_id: `ws-${Math.random().toString(36).slice(2, 8)}`,
    created_at: now.toISOString(),
  };
  const tasks = [newTask, ...loadTasks()];
  persistTasks(tasks);
  return newTask;
}

export async function getTaskDetail(taskId: string): Promise<TaskDetail> {
  const tasks = loadTasks();
  const task = tasks.find((t) => t.id === taskId);
  if (!task) {
    throw new Error(`Task ${taskId} not found`);
  }
  return {
    task,
    events: buildEvents(task),
    features: buildFeatures(task),
    progress: buildProgress(task),
    files: buildFiles(task),
    evals: buildEvaluations(task),
  };
}

export async function runTaskAction(
  taskId: string,
  action: "init" | "coding" | "eval",
): Promise<{ message: string; updated: TaskSummary }> {
  const tasks = loadTasks();
  const index = tasks.findIndex((t) => t.id === taskId);
  if (index === -1) {
    throw new Error(`Task ${taskId} not found`);
  }

  const task = tasks[index];
  let status = task.status;
  let message = "";

  switch (action) {
    case "init":
      status = "initialized";
      message = "Initializer finished (3 files written)";
      break;
    case "coding":
      status = "running";
      message = "Coding sessions: 2, remaining failing features: 1";
      break;
    case "eval":
      status = "completed";
      message = "Evaluation completed (score: 0.92)";
      break;
    default:
      status = task.status;
      message = "Action completed";
  }

  const updated: TaskSummary = { ...task, status };
  tasks[index] = updated;
  persistTasks(tasks);
  return { message, updated };
}

function buildEvents(task: TaskSummary): TimelineEvent[] {
  const baseEvents: TimelineEvent[] = [
    {
      id: `${task.id}-created`,
      session_type: "system",
      agent_role: "Initializer",
      event_type: "task_created",
      payload: { text: task.goal },
      created_at: task.created_at,
    },
    {
      id: `${task.id}-init`,
      session_type: "init",
      agent_role: "Initializer",
      event_type: "files_written",
      payload: { count: 3, text: "Scaffolded workspace" },
      created_at: addSeconds(task.created_at, 60),
    },
  ];

  if (task.status === "running" || task.status === "completed") {
    baseEvents.push({
      id: `${task.id}-coding`,
      session_type: "coding",
      agent_role: "CodingAgent",
      event_type: "patch_applied",
      payload: { text: "Implemented core workflow logic" },
      created_at: addSeconds(task.created_at, 120),
    });
  }

  if (task.status === "completed") {
    baseEvents.push({
      id: `${task.id}-eval`,
      session_type: "evaluation",
      agent_role: "EvalAgent",
      event_type: "score_reported",
      payload: { score: 0.92, text: "All checks passed" },
      created_at: addSeconds(task.created_at, 180),
    });
  }

  return baseEvents;
}

function buildFeatures(task: TaskSummary): Feature[] {
  return [
    {
      id: "F-101",
      description: `Align output with goal: ${task.goal}`,
      status: task.status === "completed" ? "done" : "pending",
      notes: "Solid frontend now mirrors task workflow",
    },
    {
      id: "F-108",
      description: "Persist workspace files to storage",
      status: task.status === "completed" ? "done" : "in-progress",
      notes: "Mocked in frontend for demo purposes",
    },
  ];
}

function buildProgress(task: TaskSummary): string {
  const lines = [
    `${task.created_at} · Created task ${task.id}`,
    `${addSeconds(task.created_at, 30)} · Waiting for initializer...`,
    `${addSeconds(task.created_at, 60)} · Initializer finished (3 files)`,
  ];

  if (task.status === "running" || task.status === "completed") {
    lines.push(`${addSeconds(task.created_at, 120)} · Coding applied patches to repo`);
  }
  if (task.status === "completed") {
    lines.push(`${addSeconds(task.created_at, 180)} · Evaluation score: 0.92`);
  }

  return lines.join("\n");
}

function buildFiles(task: TaskSummary): string[] {
  const base = [
    `${task.workspace_id}/README.md`,
    `${task.workspace_id}/app/main.py`,
    `${task.workspace_id}/frontend/index.tsx`,
  ];
  if (task.status !== "pending") {
    base.push(`${task.workspace_id}/tests/test_app.py`);
  }
  return base;
}

function buildEvaluations(task: TaskSummary): EvalResult[] {
  if (task.status !== "completed") return [];
  return [
    {
      feature_id: "F-101",
      status: "pass",
      evidence: "Goal matched user prompt and assets generated",
      started_at: addSeconds(task.created_at, 160),
      completed_at: addSeconds(task.created_at, 180),
    },
  ];
}

function addSeconds(timestamp: string, seconds: number): string {
  const date = new Date(timestamp);
  date.setSeconds(date.getSeconds() + seconds);
  return date.toISOString();
}
