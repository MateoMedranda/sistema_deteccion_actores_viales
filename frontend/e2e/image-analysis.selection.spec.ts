import { test, expect } from "@playwright/test";
import { complete } from "./helpers";
test("overlay and accessible list share selection without changing focus", async ({
  page,
}) => {
  await complete(page);
  const second = page.getByRole("button", {
    name: "Detección 2, Camión",
    exact: true,
  });
  await second.focus();
  await page.keyboard.press("Enter");
  await expect(second).toBeFocused();
  await expect(second).toHaveAttribute("aria-pressed", "true");
  await expect(
    page
      .getByRole("complementary", { name: "Ficha del vehículo" })
      .getByRole("heading", { name: "Detección 2", exact: true }),
  ).toBeVisible();
  const first = page.locator(".detection-list button").first();
  await first.focus();
  await page.keyboard.press("Space");
  await expect(first).toHaveAttribute("aria-pressed", "true");
  await expect(second).toHaveAttribute("aria-pressed", "false");
  const scene = page.locator(".scene-viewer img");
  const image = await scene.boundingBox(),
    overlay = await page.locator(".scene-viewer button").first().boundingBox();
  expect(image).not.toBeNull();
  expect(overlay!.x).toBeGreaterThanOrEqual(image!.x);
  expect(overlay!.x + overlay!.width).toBeLessThanOrEqual(
    image!.x + image!.width + 1,
  );
});

import { mockScenario } from "./scenarios";
import { analyze } from "./helpers";
test("selection is available while enrichment is processing", async ({
  page,
}) => {
  await mockScenario(page, "enriching");
  await analyze(page);
  await page.locator(".detection-list button").nth(1).click();
  await expect(page.locator(".detection-list button").nth(1)).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await expect(
    page.getByText("Consultando atributos\u2026", { exact: true }),
  ).toBeVisible();
});
