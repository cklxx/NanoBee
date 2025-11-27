export type EvalResult = {
  id: number;
  score: number;
  details: string;
  created_at?: string;
};

export function EvaluationPanel({ results }: { results: EvalResult[] }) {
  return (
    <div className="card space-y-2">
      <h3 className="text-lg font-semibold">Evaluation</h3>
      {results.length === 0 ? (
        <p className="text-sm text-slate-600">No evaluations recorded yet. Trigger the /evaluate endpoint.</p>
      ) : (
        <ul className="space-y-2">
          {results.map((r) => (
            <li key={r.id} className="border border-slate-200 rounded p-3 bg-slate-50">
              <div className="flex items-center justify-between text-sm">
                <span className="font-semibold">Score: {r.score}</span>
                <span className="text-slate-500">{r.created_at}</span>
              </div>
              <p className="text-sm text-slate-700 mt-1 whitespace-pre-wrap">{r.details}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
