import { defineConfig, devices } from "@playwright/test";

const FRONTEND_PORT = process.env.FRONTEND_PORT || "3000";
const BACKEND_PORT = process.env.BACKEND_PORT || "8000";

export default defineConfig({
  testDir: "./e2e",
  timeout: 120_000,
  expect: {
    timeout: 10_000,
  },
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  use: {
    baseURL: `http://127.0.0.1:${FRONTEND_PORT}`,
    trace: "on-first-retry",
  },
  webServer: {
    command: `BACKEND_PORT=${BACKEND_PORT} FRONTEND_PORT=${FRONTEND_PORT} NEXT_PUBLIC_API_BASE=http://127.0.0.1:${BACKEND_PORT} ../scripts/run_fullstack.sh`,
    url: `http://127.0.0.1:${FRONTEND_PORT}`,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
