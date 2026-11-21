import { test, expect } from "@playwright/test";
test("isolated API and frontend start", async ({ page, request }) => {
  const ready = await request.get(
    "http://127.0.0.1:8767/health/enrichment-ready",
  );
  expect(ready.status()).toBe(200);
  await page.goto("/");
  await expect(page.locator("main")).toBeVisible();
});
