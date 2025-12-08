import { createRootRoute, createRoute, createRouter } from "@tanstack/solid-router";
import { HomePage } from "@/screens/HomePage";
import { GuideVolcenginePage } from "@/screens/GuideVolcenginePage";
import { RootLayout } from "@/shared/RootLayout";

const rootRoute = createRootRoute({
  component: RootLayout,
});

const homeRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  component: HomePage,
});

const guideRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/guide/volcengine",
  component: GuideVolcenginePage,
});

const routeTree = rootRoute.addChildren([homeRoute, guideRoute]);

export const router = createRouter({
  routeTree,
  defaultPreload: "intent",
});

declare module "@tanstack/solid-router" {
  interface Register {
    router: typeof router;
  }
}
