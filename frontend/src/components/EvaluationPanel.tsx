import { For, Show } from "solid-js";

export type EvalResult = {
  feature_id: string;
  status: string;
  evidence?: string;
  started_at?: string;
  completed_at?: string;
};

export function EvaluationPanel(props: { results: EvalResult[] }) {
  return (
    <div class="card space-y-3">
      <div>
        <h3 class="text-lg font-semibold">Evaluation</h3>
        <p class="text-sm text-slate-600">Auto-evaluated after coding sessions finish</p>
      </div>
      <Show when={props.results.length} fallback={<p class="text-sm text-slate-600">No evaluation results yet.</p>}>
        <div class="space-y-2">
          <For each={props.results}>
            {(result) => (
              <div class="border border-slate-200 rounded-lg p-3 bg-slate-50">
                <div class="flex items-center justify-between text-sm">
                  <div class="flex items-center gap-2">
                    <span class="px-2 py-1 bg-slate-900 text-white rounded text-xs">{result.status}</span>
                    <span class="font-semibold">Feature {result.feature_id}</span>
                  </div>
                  <span class="text-slate-500">
                    {result.started_at} → {result.completed_at}
                  </span>
                </div>
                <p class="text-sm mt-1 text-slate-700">{result.evidence}</p>
              </div>
            )}
          </For>
        </div>
      </Show>
    </div>
  );
}
