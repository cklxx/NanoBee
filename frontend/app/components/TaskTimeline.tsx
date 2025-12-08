export type TimelineEvent = {
  id: string;
  session_type: string;
  agent_role: string;
  event_type: string;
  payload?: Record<string, unknown> | null;
  created_at?: string;
};

export function TaskTimeline({ events }: { events: TimelineEvent[] }) {
  if (!events.length) {
    return <div className="card">No events yet. Trigger initializer or coding sessions to populate the timeline.</div>;
  }
  const primaryAgents = new Set(["Initializer", "CodingAgent", "EvalAgent"]);
  const sorted = [...events].sort((a, b) => (a.created_at ?? "").localeCompare(b.created_at ?? ""));
  return (
    <div className="card space-y-4">
      <h3 className="text-lg font-semibold">Timeline</h3>
      <ul className="space-y-3">
        {sorted.map((event) => {
          const isSubAgent = !primaryAgents.has(event.agent_role);
          const humanPayload =
            event.payload && typeof event.payload === "object" && "text" in event.payload
              ? String((event.payload as any).text)
              : null;
          return (
            <li key={event.id} className="border border-slate-200 rounded-lg p-3 bg-slate-50">
              <div className="flex items-center justify-between text-sm text-slate-700">
                <div className="flex items-center gap-2">
                  <span className="font-semibold">{event.agent_role}</span>
                  {isSubAgent ? (
                    <span className="px-2 py-0.5 text-xs rounded-full bg-indigo-100 text-indigo-800 border border-indigo-200">
                      Sub-agent
                    </span>
                  ) : null}
                </div>
                <span className="text-slate-500">{event.created_at}</span>
              </div>
              <p className="text-sm mt-1">
                {event.session_type} / {event.event_type}
              </p>
              {humanPayload ? <p className="text-xs text-slate-700 mt-1">{humanPayload}</p> : null}
              {event.payload && !humanPayload ? (
                <pre className="mt-2 text-xs bg-white border border-slate-200 rounded p-2 overflow-x-auto">
                  {JSON.stringify(event.payload, null, 2)}
                </pre>
              ) : null}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
