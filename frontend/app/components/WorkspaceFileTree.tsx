export function WorkspaceFileTree({ files }: { files: string[] }) {
  if (!files.length) {
    return <div className="card">No files yet. Run initializer to generate scaffold.</div>;
  }
  return (
    <div className="card">
      <h3 className="text-lg font-semibold mb-2">Workspace Files</h3>
      <ul className="space-y-1 text-sm font-mono">
        {files.map((file) => (
          <li key={file} className="text-slate-700">
            {file}
          </li>
        ))}
      </ul>
    </div>
  );
}
