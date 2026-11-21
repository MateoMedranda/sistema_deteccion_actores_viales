import { test, expect } from "@playwright/test";
import { complete } from "./helpers";
test("capture actual initial and completed states for manual review", async ({
  page,
}, testInfo) => {
  await page.goto("/");
  await page.screenshot({
    path: testInfo.outputPath("initial.png"),
    fullPage: true,
  });
  await complete(page);
  await expect(
    page.getByRole("img", { name: "Recorte de la placa", exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: testInfo.outputPath("completed.png"),
    fullPage: true,
  });
});
