import { For, Show, createMemo } from "solid-js";

export type TimelineEvent = {
  id: string;
  session_type: string;
  agent_role: string;
  event_type: string;
  payload?: Record<string, unknown> | null;
  created_at?: string;
};

export function TaskTimeline(props: { events: TimelineEvent[] }) {
  const primaryAgents = new Set(["Initializer", "CodingAgent", "EvalAgent"]);
  const sorted = createMemo(() => [...props.events].sort((a, b) => (a.created_at ?? "").localeCompare(b.created_at ?? "")));

  return (
    <div class="card space-y-4">
      <h3 class="text-lg font-semibold">Timeline</h3>
      <Show when={props.events.length} fallback={<div class="text-sm text-slate-600">No events yet. Trigger initializer or coding sessions to populate the timeline.</div>}>
        <ul class="space-y-3">
          <For each={sorted()}>
            {(event) => {
              const humanPayload =
                event.payload && typeof event.payload === "object" && "text" in event.payload
                  ? String((event.payload as any).text)
                  : null;
              const isSubAgent = !primaryAgents.has(event.agent_role);
              return (
                <li class="border border-slate-200 rounded-lg p-3 bg-slate-50">
                  <div class="flex items-center justify-between text-sm text-slate-700">
                    <div class="flex items-center gap-2">
                      <span class="font-semibold">{event.agent_role}</span>
                      <Show when={isSubAgent}>
                        <span class="px-2 py-0.5 text-xs rounded-full bg-indigo-100 text-indigo-800 border border-indigo-200">Sub-agent</span>
                      </Show>
                    </div>
                    <span class="text-slate-500">{event.created_at}</span>
                  </div>
                  <p class="text-sm mt-1">
                    {event.session_type} / {event.event_type}
                  </p>
                  <Show when={humanPayload}>
                    <p class="text-xs text-slate-700 mt-1">{humanPayload}</p>
                  </Show>
                  <Show when={event.payload && !humanPayload}>
                    <pre class="mt-2 text-xs bg-white border border-slate-200 rounded p-2 overflow-x-auto">
                      {JSON.stringify(event.payload, null, 2)}
                    </pre>
                  </Show>
                </li>
              );
            }}
          </For>
        </ul>
      </Show>
    </div>
  );
}
