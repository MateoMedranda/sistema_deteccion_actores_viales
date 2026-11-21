import { test, expect } from "@playwright/test";
import path from "node:path";
import { connect } from "./helpers";
for (const action of ["reset", "credential", "service"]) {
  test(
    "invalidating " + action + " aborts an upload before its job ID exists",
    async ({ page }) => {
      let release!: () => void;
      const gate = new Promise<void>((r) => (release = r));
      let arrived!: () => void;
      const started = new Promise<void>((r) => (arrived = r));
      let aborted = false;
      page.on("requestfailed", (r) => {
        if (r.method() === "POST" && r.url().endsWith("/video-jobs"))
          aborted = true;
      });
      await page.route("**/api/v1/video-jobs", async (route) => {
        arrived();
        await gate;
        await route
          .fulfill({
            status: 202,
            json: {
              job_id: "late",
              status: "queued",
              expires_at: new Date(Date.now() + 300000).toISOString(),
            },
          })
          .catch(() => {});
      });
      await connect(page);
      await page
        .getByText("Herramientas de video y conteo", { exact: true })
        .click();
      await page
        .getByLabel("Video", { exact: true })
        .setInputFiles(path.resolve("e2e/fixtures/controlled.mp4"));
      await page
        .getByRole("button", { name: "Procesar video", exact: true })
        .click();
      await started;
      await page.getByText("Configurar sesión", { exact: true }).click();
      if (action === "reset")
        await page
          .getByRole("button", { name: "Reiniciar demostración" })
          .click();
      else if (action === "credential")
        await page
          .getByLabel("API key", { exact: true })
          .fill("new-synthetic-key");
      else await page.getByLabel("URL backend").fill("http://localhost:8767");
      await expect.poll(() => aborted).toBe(true);
      await expect(page.locator(".line-editor")).toHaveCount(0);
      release();
      await expect(page.getByText("late", { exact: true })).toHaveCount(0);
    },
  );
}
test("failed remote cancellation still clears the session immediately", async ({
  page,
}) => {
  let cancelled = false;
  await page.route("**/api/v1/video-jobs*", async (route) => {
    if (route.request().method() === "POST")
      return route.fulfill({
        status: 202,
        json: {
          job_id: "active-job",
          status: "queued",
          expires_at: new Date(Date.now() + 300000).toISOString(),
        },
      });
    return route.fulfill({
      json: {
        job_id: "active-job",
        status: "processing",
        expires_at: new Date(Date.now() + 300000).toISOString(),
      },
    });
  });
  await page.route("**/api/v1/video-jobs/active-job", async (route) => {
    if (route.request().method() === "DELETE") {
      cancelled = true;
      return route.fulfill({ status: 503, json: { code: "unavailable" } });
    }
    return route.fulfill({
      json: {
        job_id: "active-job",
        status: "processing",
        expires_at: new Date(Date.now() + 300000).toISOString(),
      },
    });
  });
  await connect(page);
  await page
    .getByText("Herramientas de video y conteo", { exact: true })
    .click();
  await page
    .getByLabel("Video", { exact: true })
    .setInputFiles(path.resolve("e2e/fixtures/controlled.mp4"));
  await page
    .getByRole("button", { name: "Procesar video", exact: true })
    .click();
  await expect(
    page.getByText("Trabajo iniciado.", { exact: false }),
  ).toContainText("queued");
  await page.getByText("Configurar sesión", { exact: true }).click();
  await page.getByRole("button", { name: "Reiniciar demostración" }).click();
  await expect(page.locator(".line-editor")).toHaveCount(0);
  await expect(page.getByLabel("API key", { exact: true })).toHaveValue("");
  await expect.poll(() => cancelled).toBe(true);
});
test("an access rejection while downloading video withdraws preview and file", async ({
  page,
}) => {
  const expires = new Date(Date.now() + 300000).toISOString();
  await page.route("**/api/v1/video-jobs", (route) =>
    route.fulfill({
      status: 202,
      json: { job_id: "denied-job", status: "queued", expires_at: expires },
    }),
  );
  await page.route("**/api/v1/video-jobs/denied-job", (route) =>
    route.fulfill({
      json: { job_id: "denied-job", status: "completed", expires_at: expires },
    }),
  );
  await page.route("**/api/v1/video-jobs/denied-job/annotated-video", (route) =>
    route.fulfill({ status: 401, json: { code: "invalid_api_key" } }),
  );
  await connect(page);
  await page
    .getByText("Herramientas de video y conteo", { exact: true })
    .click();
  await page
    .getByLabel("Video", { exact: true })
    .setInputFiles(path.resolve("e2e/fixtures/controlled.mp4"));
  await page
    .getByRole("button", { name: "Procesar video", exact: true })
    .click();
  await expect(
    page.getByText("Acceso rechazado. Revisa la credencial de sesión.", {
      exact: false,
    }),
  ).toBeVisible();
  await expect(page.locator(".line-editor")).toHaveCount(0);
  await expect(page.getByLabel("Video", { exact: true })).toHaveValue("");
});
