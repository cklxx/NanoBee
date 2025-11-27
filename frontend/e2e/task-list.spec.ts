import { test, expect } from "@playwright/test";

const GOAL_TEXT = "Playwright e2e task";

test("home page loads and can create a task", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Create task" })).toBeVisible();

  await page.getByPlaceholder("Describe the task goal").fill(GOAL_TEXT);
  await page.getByRole("button", { name: "Create", exact: true }).click();

  await expect(page.getByText(GOAL_TEXT)).toBeVisible({ timeout: 20000 });
});
