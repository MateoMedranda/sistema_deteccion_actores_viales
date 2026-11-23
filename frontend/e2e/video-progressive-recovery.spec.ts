import { test, expect } from "@playwright/test";
import path from "node:path";
async function start(
  page: any,
  request: any,
  scenario: string,
  clip = "source",
) {
  await request.post(
    "http://127.0.0.1:9415/test-only/reset?scenario=" + scenario,
  );
  await page.goto("/");
  await expect(page.locator("main")).toHaveAttribute(
    "data-session-state",
    "ready",
  );
  await page.getByRole("tab", { name: "Video", exact: true }).click();
  await page
    .locator('input[type="file"][aria-label="Video"]')
    .setInputFiles(path.resolve("../.runtime/e2e-009/" + clip + ".mp4"));
  await page
    .getByRole("button", { name: "Procesar video", exact: true })
    .click();
}
test("short empty clips play and a manual pause survives progress updates", async ({
  page,
  request,
}) => {
  await start(page, request, "empty", "short");
  const canvas = page.locator(".progressive-surface canvas");
  await expect(canvas).toBeVisible();
  if (!(await page.evaluate(() => typeof VideoDecoder === "function"))) {
    await expect(
      page.getByText(/La reproducción progresiva no es compatible/),
    ).toBeVisible();
    await page
      .getByRole("button", { name: "Limpiar video", exact: true })
      .click();
    return;
  }
  await expect
    .poll(async () => Number(await canvas.getAttribute("data-time-us")))
    .toBeGreaterThan(0);
  await page
    .getByRole("button", { name: "Pausar e inspeccionar", exact: true })
    .click();
  await page.waitForTimeout(700);
  await expect(page.locator(".progressive-viewer [role=status]")).toContainText(
    "En pausa",
  );
  await expect(page.locator(".progressive-track-list button")).toHaveCount(0);
  await page
    .getByRole("button", { name: "Limpiar video", exact: true })
    .click();
});
test("technical failure retains its prefix, reconnects, then access rejection clears it", async ({
  page,
  request,
}) => {
  await start(page, request, "fault");
  const canvas = page.locator(".progressive-surface canvas");
  await expect(canvas).toBeVisible();
  await expect(page.getByText(/El análisis se interrumpió/)).toBeVisible({
    timeout: 15000,
  });
  await page
    .getByRole("button", { name: "Pausar e inspeccionar", exact: true })
    .click();
  const slider = page.getByRole("slider", { name: /Posición del video/ });
  await slider.focus();
  await page.keyboard.press("End");
  expect(Number(await slider.inputValue())).toBeLessThan(6_000_000);
  let attempts = 0;
  await page.route("**/playback", (route) => {
    if (route.request().method() === "GET" && attempts++ === 0)
      return route.abort("failed");
    return route.continue();
  });
  await expect(page.getByText(/Reconectando automáticamente/)).toBeVisible();
  await expect(page.getByText(/El análisis se interrumpió/)).toBeVisible({
    timeout: 10000,
  });
  await page.unroute("**/playback");
  await page.route("**/playback", (route) =>
    route.fulfill({
      status: 410,
      json: { code: "artifact_expired", message: "Expired" },
    }),
  );
  await expect(canvas).toHaveCount(0, { timeout: 10000 });
});
test("unsupported frame callbacks never expose native playback", async ({
  page,
  request,
}) => {
  await page.addInitScript(() => {
    Object.defineProperty(window, "VideoDecoder", {
      value: undefined,
      configurable: true,
    });
  });
  await start(page, request, "empty", "short");
  await expect(
    page.getByText(
      "La reproducción progresiva no es compatible con este navegador o formato. Puedes consultar los datos analizados.",
      { exact: false },
    ),
  ).toBeVisible();
  expect(await page.locator(".progressive-surface video").count()).toBe(0);
  await page
    .getByRole("button", { name: "Limpiar video", exact: true })
    .click();
});

test.afterEach(async ({ request }) => {
  await request.post("http://127.0.0.1:9415/test-only/release");
});
