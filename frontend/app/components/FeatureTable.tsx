export type Feature = {
  id: string;
  description: string;
  status: string;
  notes?: string;
};

export function FeatureTable({ features }: { features: Feature[] }) {
  if (!features.length) {
    return <div className="card">feature_list.json not found yet. Run initializer first.</div>;
  }
  return (
    <div className="card">
      <h3 className="text-lg font-semibold mb-2">Features</h3>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="text-left text-slate-600 border-b">
              <th className="py-2 pr-4">ID</th>
              <th className="py-2 pr-4">Description</th>
              <th className="py-2 pr-4">Status</th>
              <th className="py-2">Notes</th>
            </tr>
          </thead>
          <tbody>
            {features.map((f) => (
              <tr key={f.id} className="border-b last:border-b-0">
                <td className="py-2 pr-4 font-mono text-xs">{f.id}</td>
                <td className="py-2 pr-4">{f.description}</td>
                <td className="py-2 pr-4">
                  <span className="px-2 py-1 text-xs rounded-full bg-slate-100 border border-slate-200">
                    {f.status}
                  </span>
                </td>
                <td className="py-2 text-slate-700 text-xs">{f.notes}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
