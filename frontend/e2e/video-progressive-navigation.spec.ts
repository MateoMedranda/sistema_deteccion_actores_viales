import { test, expect } from "@playwright/test";
import path from "node:path";
test("plays the confirmed prefix, blocks future seeks and inspects ten stable tracks", async ({
  page,
  request,
}, testInfo) => {
  await request.post("http://127.0.0.1:9415/test-only/reset");
  const posts: string[] = [];
  page.on("request", (r) => {
    if (r.method() === "POST") posts.push(r.url());
  });
  await page.goto("/");
  await expect(page.locator("main")).toHaveAttribute(
    "data-session-state",
    "ready",
  );
  await page.getByRole("tab", { name: "Video", exact: true }).click();
  await page
    .locator('input[type="file"][aria-label="Video"]')
    .setInputFiles(path.resolve("../.runtime/e2e-009/source.mp4"));
  await page
    .getByRole("button", { name: "Procesar video", exact: true })
    .click();
  const canvas = page.locator(".progressive-surface canvas");
  await expect(canvas).toBeVisible({ timeout: 20000 });
  if (!(await page.evaluate(() => typeof VideoDecoder === "function"))) {
    await expect(
      page.getByText(/La reproducción progresiva no es compatible/),
    ).toBeVisible();
    expect(await page.locator(".progressive-surface video").count()).toBe(0);
    testInfo.annotations.push({
      type: "compatibility",
      description:
        "WebCodecs unavailable: safe fallback only; playback gate remains unverified.",
    });
    await request.post("http://127.0.0.1:9415/test-only/release");
    await page
      .getByRole("button", { name: "Limpiar video", exact: true })
      .click();
    return;
  }
  await expect
    .poll(() => canvas.getAttribute("data-frame-index"))
    .not.toBeNull();
  const firstObserved = Date.now();
  const job = await canvas.getAttribute("data-job-id");
  const commit = (
    await (
      await request.get("http://127.0.0.1:9415/test-only/metrics?job=" + job)
    ).json()
  ).five_seconds_commit_ms;
  expect(commit).toBeGreaterThan(0);
  expect(firstObserved - commit).toBeLessThanOrEqual(2000);
  const metrics: any = {
    initial_commit_to_observed_ms: firstObserved - commit,
    seek_ms: [],
  };
  const pixel = await canvas.evaluate((c: HTMLCanvasElement) => ({
    index: Number(c.dataset.frameIndex),
    red: c.getContext("2d")!.getImageData(5, 5, 1, 1).data[0],
  }));
  expect(
    Math.min(
      ...[-1, 0, 1].map((offset) =>
        Math.abs(pixel.red - (((pixel.index + offset) * 12) % 255)),
      ),
    ),
    JSON.stringify(pixel),
  ).toBeLessThanOrEqual(3);
  await page
    .getByRole("button", { name: "Pausar e inspeccionar", exact: true })
    .click();
  const slider = page.getByRole("slider", { name: /Posición del video/ });
  await slider.focus();
  await page.keyboard.press("End");
  await expect
    .poll(async () => Number(await slider.inputValue()))
    .toBeLessThan(6_000_001);
  const initial = Number(await slider.inputValue());
  await slider.evaluate((e: HTMLInputElement) => {
    e.value = e.max;
    e.dispatchEvent(new Event("change", { bubbles: true }));
    e.dispatchEvent(new Event("input", { bubbles: true }));
  });
  await expect
    .poll(async () => Number(await slider.inputValue()))
    .toBeLessThan(6_000_001);
  await slider.focus();
  await page.keyboard.press("Home");
  await expect
    .poll(async () => Number(await slider.inputValue()))
    .toBeLessThan(100000);
  await expect(page.locator(".progressive-track-list button")).toHaveCount(10);
  const boxButton = page.getByRole("button", {
    name: /^Consultar vehículo 3,/,
  });
  if (testInfo.project.use.hasTouch) await boxButton.tap();
  else await boxButton.click();
  await expect(
    page.getByRole("heading", { name: "Vehículo #3", exact: true }),
  ).toBeVisible();
  for (let i = 0; i < 10; i++) {
    await page.locator(".progressive-track-list button").nth(i).click();
    await expect(
      page.getByRole("heading", { name: "Vehículo #" + (i + 1), exact: true }),
    ).toBeVisible();
  }
  if (await page.evaluate(() => document.fullscreenEnabled)) {
    await page
      .getByRole("button", { name: "Pantalla completa", exact: true })
      .click();
    await expect
      .poll(() => page.evaluate(() => document.fullscreenElement?.className))
      .toContain("progressive-viewer");
    await page.keyboard.press("Escape");
    await expect
      .poll(() => page.evaluate(() => document.fullscreenElement === null))
      .toBe(true);
  }
  await expect(
    page.getByRole("heading", { name: "Vehículo #10", exact: true }),
  ).toBeVisible();
  await expect(page.getByText("SYN123", { exact: true })).toBeVisible({
    timeout: 15000,
  });
  await expect(
    page.getByRole("img", { name: "Recorte del vehículo", exact: true }),
  ).toBeVisible();
  const before = posts.length;
  for (let i = 0; i < 30; i++) {
    const started = Date.now();
    await slider.focus();
    await page.keyboard.press(i % 2 ? "Home" : "End");
    await expect
      .poll(async () => Number(await canvas.getAttribute("data-frame-index")), {
        timeout: 2000,
        intervals: [10, 20, 50],
      })
      .toBe(i % 2 ? 0 : 179);
    metrics.seek_ms.push(Date.now() - started);
  }
  expect(
    metrics.seek_ms.filter((ms: number) => ms < 1000).length,
  ).toBeGreaterThanOrEqual(29);
  expect(posts).toHaveLength(before);
  await page.evaluate(() => (document.documentElement.style.fontSize = "200%"));
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: testInfo.outputPath("progressive.png"),
    fullPage: true,
  });
  await request.post("http://127.0.0.1:9415/test-only/release");
  await page.getByRole("button", { name: "Reproducir", exact: true }).click();
  await expect
    .poll(async () => Number(await canvas.getAttribute("data-time-us")))
    .toBeGreaterThan(0);
  metrics.unique_frames_in_available_five_seconds = await canvas.evaluate(
    async (c: HTMLCanvasElement) => {
      const seen = new Set<number>();
      const observer = new MutationObserver(() =>
        seen.add(Number(c.dataset.frameIndex)),
      );
      observer.observe(c, {
        attributes: true,
        attributeFilter: ["data-frame-index"],
      });
      await new Promise((r) => setTimeout(r, 5000));
      observer.disconnect();
      return seen.size;
    },
  );
  await testInfo.attach("controlled-metrics", {
    body: JSON.stringify(metrics),
    contentType: "application/json",
  });
  expect(
    metrics.unique_frames_in_available_five_seconds,
  ).toBeGreaterThanOrEqual(135);
  await page.evaluate(() => {
    const end = performance.now() + 1500;
    while (performance.now() < end) {}
  });
  expect(Number(await canvas.getAttribute("data-time-us"))).toBeLessThanOrEqual(
    Number(await canvas.getAttribute("data-admitted-until-us")),
  );
  expect(
    posts.filter((u) => u.includes("/video-jobs?presentation=progressive")),
  ).toHaveLength(1);
  expect(posts.filter((u) => u.endsWith("/enrichment-jobs"))).toHaveLength(0);
  await page
    .getByRole("button", { name: "Limpiar video", exact: true })
    .click();
  await expect(canvas).toHaveCount(0);
});

test.afterEach(async ({ request }) => {
  await request.post("http://127.0.0.1:9415/test-only/release");
});
