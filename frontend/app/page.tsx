import { CreateTaskForm } from "./components/CreateTaskForm";
import { TaskList, TaskSummary } from "./components/TaskList";

const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

async function fetchTasks(): Promise<{ tasks: TaskSummary[]; error?: string }> {
  try {
    const res = await fetch(`${apiBase}/api/tasks`, { cache: "no-store" });
    if (!res.ok) {
      return { tasks: [], error: `Backend responded with ${res.status}` };
    }
    const data = await res.json();
    return { tasks: data };
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    console.error("Failed to fetch tasks from backend", err);
    return { tasks: [], error: message };
  }
}

export default async function HomePage() {
  const { tasks, error } = await fetchTasks();
  return (
    <main className="space-y-4">
      {error ? (
        <div className="card border-red-200 bg-red-50 text-sm text-red-800" role="alert">
          Unable to reach backend API ({error}). Verify the server is running and NEXT_PUBLIC_API_BASE is set correctly.
        </div>
      ) : null}
      <CreateTaskForm />
      <TaskList tasks={tasks} />
      <p className="text-sm text-slate-600">
        Use the API to create tasks and trigger initializer/coding sessions. This console reads data directly from the
        backend without additional state management.
      </p>
    </main>
  );
}
