import { readFileSync } from "node:fs";
import path from "node:path";
import { test, expect } from "@playwright/test";
import { connect, scene, analyze } from "./helpers";
import { scenes, serveScenes, chooseScene } from "./exploration";
test("actual overlay focus remains visible over white and black pixels", async ({
  page,
}, testInfo) => {
  await serveScenes(page, [scenes[0]]);
  await connect(page);
  await chooseScene(page, scenes[0]);
  const control = page.locator(".scene-viewer button").first();
  for (const background of ["rgb(255, 255, 255)", "rgb(0, 0, 0)"]) {
    await page.locator(".scene-viewer").evaluate((el, bg) => {
      (el as HTMLElement).style.background = bg;
    }, background);
    await page.locator(".scene-viewer img").evaluate((el) => {
      (el as HTMLElement).style.opacity = "0";
    });
    await control.focus();
    await expect(control).toBeFocused();
    const colors = await control.evaluate((el) => {
      const s = getComputedStyle(el);
      return [
        s.outlineColor,
        s.borderTopColor,
        ...(s.boxShadow.match(/rgb\([^)]+\)/g) ?? []),
      ];
    });
    const lum = (c: string) =>
      c
        .match(/[\d.]+/g)!
        .slice(0, 3)
        .map(Number)
        .map((n) => n / 255)
        .map((s) => (s <= 0.04045 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4))
        .reduce((sum, n, i) => sum + n * [0.2126, 0.7152, 0.0722][i], 0);
    const b = lum(background),
      contrast = Math.max(
        ...colors.map((color) => {
          const a = lum(color);
          return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
        }),
      );
    expect(contrast).toBeGreaterThanOrEqual(3);
    await page.screenshot({
      path: testInfo.outputPath(
        background.includes("255") ? "focus-light.png" : "focus-dark.png",
      ),
      fullPage: true,
    });
  }
  await control.click();
  expect(
    await control.evaluate((el) => getComputedStyle(el, "::after").content),
  ).toBe("none");
});
test("overlapping and tiny boxes remain selectable through touch alternatives", async ({
  page,
}, testInfo) => {
  const original = scenes[0],
    overlap = {
      ...original,
      detections: original.detections.map((d: any) => ({
        ...d,
        bbox: { ...original.detections[0].bbox },
      })),
    };
  const tiny = {
    ...original,
    detections: original.detections.map((d: any, i: number) =>
      i ? { ...d, bbox: { x_min: 1, y_min: 1, x_max: 2, y_max: 2 } } : d,
    ),
  };
  await serveScenes(page, [overlap, tiny]);
  await connect(page);
  for (const scene of [overlap, tiny]) {
    await chooseScene(page, scene);
    for (let index = 0; index < 2; index++) {
      const control = page.locator(".detection-list button").nth(index);
      if (testInfo.project.name !== "desktop") await control.tap();
      else await control.click();
      await expect(page.locator(".vehicle-details h3")).toHaveText(
        "Detección " + scene.detections[index].detection_id,
      );
    }
  }
});
test("original media can recover from undecodable bytes without another POST", async ({
  page,
}) => {
  let attempts = 0,
    posts = 0;
  await serveScenes(page, [scenes[0]]);
  await page.route("**/original-image", async (route) => {
    attempts++;
    return route.fulfill({
      contentType: "image/png",
      body:
        attempts === 1
          ? Buffer.from("invalid image")
          : readFileSync(path.resolve("e2e/fixtures/exploration/scene-0.png")),
    });
  });
  page.on("request", (r) => {
    if (r.method() === "POST" && r.url().endsWith("/images")) posts++;
  });
  await connect(page);
  await chooseScene(page, scenes[0]);
  await expect(
    page.getByText("La escena original no está disponible.", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Reintentar original", exact: true })
    .click();
  await expect(page.locator(".scene-viewer img")).toBeVisible();
  expect(posts).toBe(1);
  expect(attempts).toBe(2);
});
