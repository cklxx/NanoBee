import Link from "next/link";

export type TaskSummary = {
  id: string;
  goal: string;
  status: string;
  workspace_id: string;
  created_at?: string;
};

export function TaskList({ tasks }: { tasks: TaskSummary[] }) {
  if (!tasks.length) {
    return <div className="card">No tasks found. Create one via the API to get started.</div>;
  }
  return (
    <div className="grid grid-cols-1 gap-3">
      {tasks.map((task) => (
        <Link key={task.id} href={`/tasks/${task.id}`} className="card block hover:border-blue-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold">{task.goal}</h3>
              <p className="text-sm text-slate-600">Task ID: {task.id}</p>
              <p className="text-sm text-slate-600">Workspace: {task.workspace_id}</p>
            </div>
            <span className="px-3 py-1 text-sm rounded-full bg-slate-100 border border-slate-200">
              {task.status}
            </span>
          </div>
        </Link>
      ))}
    </div>
  );
}
