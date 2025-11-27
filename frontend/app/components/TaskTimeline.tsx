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
  return (
    <div className="card space-y-4">
      <h3 className="text-lg font-semibold">Timeline</h3>
      <ul className="space-y-3">
        {events.map((event) => (
          <li key={event.id} className="border border-slate-200 rounded-lg p-3 bg-slate-50">
            <div className="flex items-center justify-between text-sm text-slate-700">
              <span className="font-semibold">{event.agent_role}</span>
              <span className="text-slate-500">{event.created_at}</span>
            </div>
            <p className="text-sm mt-1">
              {event.session_type} / {event.event_type}
            </p>
            {event.payload && (
              <pre className="mt-2 text-xs bg-white border border-slate-200 rounded p-2 overflow-x-auto">
                {JSON.stringify(event.payload, null, 2)}
              </pre>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
