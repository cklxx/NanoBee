import { createRouter, Route, RootRoute } from "@tanstack/solid-router";
import { lazy } from "solid-js";
import { Layout } from "./components/Layout";
import { HomePage } from "./pages/HomePage";

const GuideVolcenginePage = lazy(() => import("./pages/GuideVolcenginePage").then((m) => ({ default: m.GuideVolcenginePage })));
const TaskDetailPage = lazy(() => import("./pages/TaskDetailPage").then((m) => ({ default: m.TaskDetailPage })));

const rootRoute = new RootRoute({ component: Layout });
const indexRoute = new Route({ getParentRoute: () => rootRoute, path: "/", component: HomePage });
const guideRoute = new Route({ getParentRoute: () => rootRoute, path: "/guide/volcengine", component: GuideVolcenginePage });
const taskRoute = new Route({ getParentRoute: () => rootRoute, path: "/tasks/$id", component: TaskDetailPage });

const routeTree = rootRoute.addChildren([indexRoute, guideRoute, taskRoute]);

export const router = createRouter({ routeTree });

declare module "@tanstack/solid-router" {
  interface Register {
    router: typeof router;
  }
}
