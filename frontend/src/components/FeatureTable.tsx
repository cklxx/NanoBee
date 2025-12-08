import { For, Show } from "solid-js";

export type Feature = {
  id: string;
  description: string;
  status: string;
  notes?: string;
};

export function FeatureTable(props: { features: Feature[] }) {
  return (
    <div class="card">
      <h3 class="text-lg font-semibold mb-2">Features</h3>
      <Show
        when={props.features.length}
        fallback={<div class="text-sm text-slate-600">feature_list.json not found yet. Run initializer first.</div>}
      >
        <div class="overflow-x-auto">
          <table class="min-w-full text-sm">
            <thead>
              <tr class="text-left text-slate-600 border-b">
                <th class="py-2 pr-4">ID</th>
                <th class="py-2 pr-4">Description</th>
                <th class="py-2 pr-4">Status</th>
                <th class="py-2">Notes</th>
              </tr>
            </thead>
            <tbody>
              <For each={props.features}>
                {(feature) => (
                  <tr class="border-b last:border-b-0">
                    <td class="py-2 pr-4 font-mono text-xs">{feature.id}</td>
                    <td class="py-2 pr-4">{feature.description}</td>
                    <td class="py-2 pr-4">
                      <span class="px-2 py-1 text-xs rounded-full bg-slate-100 border border-slate-200">{feature.status}</span>
                    </td>
                    <td class="py-2 text-slate-700 text-xs">{feature.notes}</td>
                  </tr>
                )}
              </For>
            </tbody>
          </table>
        </div>
      </Show>
    </div>
  );
}
