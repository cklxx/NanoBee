import { CreateTaskForm } from "./components/CreateTaskForm";
import { TaskList, TaskSummary } from "./components/TaskList";

const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

async function fetchTasks(): Promise<TaskSummary[]> {
  const res = await fetch(`${apiBase}/api/tasks`, { cache: "no-store" });
  if (!res.ok) {
    return [];
  }
  return res.json();
}

export default async function HomePage() {
  const tasks = await fetchTasks();
  return (
    <main className="space-y-4">
      <CreateTaskForm />
      <TaskList tasks={tasks} />
      <p className="text-sm text-slate-600">
        Use the API to create tasks and trigger initializer/coding sessions. This console reads data directly from the
        backend without additional state management.
      </p>
    </main>
  );
}
