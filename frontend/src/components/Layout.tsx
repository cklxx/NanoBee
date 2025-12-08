import { Link, Outlet } from "@tanstack/solid-router";
import { JSX } from "solid-js";
import { apiBase } from "../lib/api";

export function Layout(): JSX.Element {
  return (
    <div class="min-h-screen">
      <header class="bg-white border-b border-slate-200">
        <div class="mx-auto max-w-6xl px-4 py-4 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="text-xl font-semibold text-slate-900">NanoBee</span>
            <span class="text-xs px-2 py-1 rounded-full bg-slate-100 text-slate-600 border">Solid + TanStack Router</span>
          </div>
          <nav class="flex items-center gap-3 text-sm text-slate-700">
            <Link to="/" class="hover:text-slate-900">主页</Link>
            <Link to="/guide/volcengine" class="hover:text-slate-900">API Key 指南</Link>
          </nav>
        </div>
      </header>
      <main class="mx-auto max-w-6xl px-4 py-6 space-y-6">
        <div class="flex items-center justify-between text-xs text-slate-600">
          <p>API Base: {apiBase}</p>
          <Link to="https://github.com/tanstack/router" target="_blank" rel="noreferrer" class="underline">
            TanStack Router
          </Link>
        </div>
        <Outlet />
      </main>
    </div>
  );
}
