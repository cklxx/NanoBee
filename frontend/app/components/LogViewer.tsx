export function LogViewer({ log }: { log: string }) {
  return (
    <div className="card">
      <h3 className="text-lg font-semibold mb-2">Progress Log</h3>
      <pre className="bg-slate-50 border border-slate-200 rounded p-3 text-xs overflow-x-auto whitespace-pre-wrap">
        {log || "No progress entries yet."}
      </pre>
    </div>
  );
}
