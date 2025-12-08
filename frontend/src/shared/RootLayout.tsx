import { Link, Outlet, useRouterState, useLocation } from "@tanstack/solid-router";
import { Show } from "solid-js";

export function RootLayout() {
  const state = useRouterState();
  const location = useLocation();
  const isActive = (to: string) => location().pathname === to;

  return (
    <div class="min-h-screen bg-slate-50 text-slate-900">
      <header class="border-b bg-white shadow-sm">
        <div class="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div class="flex items-center gap-6">
            <Link to="/" class="text-xl font-semibold text-slate-800">
              NanoBee
            </Link>
            <nav class="flex items-center gap-4 text-sm">
              <Link to="/" class={isActive("/") ? "font-semibold" : "text-slate-600"}>
                首页
              </Link>
              <Link
                to="/guide/volcengine"
                class={isActive("/guide/volcengine") ? "font-semibold" : "text-slate-600"}
              >
                火山引擎指南
              </Link>
            </nav>
          </div>
          <Show when={state().status === "pending"}>
            <span class="text-xs text-slate-500">Loading...</span>
          </Show>
        </div>
      </header>
      <Outlet />
    </div>
  );
}
