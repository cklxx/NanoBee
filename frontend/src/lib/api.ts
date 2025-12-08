const env = import.meta.env;

export const apiBase =
  (env?.VITE_API_BASE as string | undefined) ||
  (env?.NEXT_PUBLIC_API_BASE as string | undefined) ||
  "http://localhost:8000";

export async function fetchJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const url = path.startsWith("http") ? path : `${apiBase}${path}`;
  const res = await fetch(url, init);
  const data = (await res.json().catch(() => ({}))) as T;
  if (!res.ok) {
    const detail = (data as any)?.detail;
    throw new Error(typeof detail === "string" ? detail : `Request failed: ${res.status}`);
  }
  return data;
}
