import { Route, RootRoute, Router } from "@tanstack/solid-router";
import { HomePage } from "@/screens/HomePage";
import { GuideVolcenginePage } from "@/screens/GuideVolcenginePage";
import { RootLayout } from "@/shared/RootLayout";

const rootRoute = new RootRoute({
  component: RootLayout,
});

const homeRoute = new Route({
  getParentRoute: () => rootRoute,
  path: "/",
  component: HomePage,
});

const guideRoute = new Route({
  getParentRoute: () => rootRoute,
  path: "/guide/volcengine",
  component: GuideVolcenginePage,
});

const routeTree = rootRoute.addChildren([homeRoute, guideRoute]);

export const router = new Router({
  routeTree,
  defaultPreload: "intent",
});

declare module "@tanstack/solid-router" {
  interface Register {
    router: typeof router;
  }
}
