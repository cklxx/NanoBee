import { For, Show } from "solid-js";

export function WorkspaceFileTree(props: { files: string[] }) {
  return (
    <div class="card">
      <h3 class="text-lg font-semibold mb-2">Workspace Files</h3>
      <Show when={props.files.length} fallback={<p class="text-sm text-slate-600">No files yet.</p>}>
        <ul class="text-sm font-mono space-y-1">
          <For each={props.files}>{(file) => <li>{file}</li>}</For>
        </ul>
      </Show>
    </div>
  );
}
