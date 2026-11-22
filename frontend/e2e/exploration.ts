import { readFileSync } from "node:fs";
import path from "node:path";
import { expect, type Page } from "@playwright/test";
const root = path.resolve("e2e/fixtures/exploration");
export const scenes: any[] = JSON.parse(
  readFileSync(path.join(root, "manifest.json"), "utf8"),
);
export async function serveScenes(page: Page, chosen: any[]) {
  let next = 0;
  const sources = new Map<string, any>(),
    jobs = new Map<string, any>();
  const pages: number[] = [];
  await page.route("**/web-api/api/**", async (route) => {
    const req = route.request(),
      url = new URL(req.url());
    const json = (body: any, status = 200) =>
      route.fulfill({ status, json: body });
    if (url.pathname.endsWith("/images")) {
      const scene = chosen[next++];
      if (!scene) throw Error("Unexpected detection POST");
      const id = "00000000-0000-4000-8000-" + String(next).padStart(12, "0"),
        expires = new Date(Date.now() + 300000).toISOString();
      sources.set(id, { scene, expires });
      return json({
        request_id: id,
        status: "completed",
        processing_time_ms: 10,
        image: { width: 640, height: 400, media_type: "image/png" },
        detections: scene.detections,
        source_expires_at: expires,
        original_image: {
          url: "/api/v1/detections/" + id + "/original-image",
          media_type: "image/png",
          expires_at: expires,
        },
        annotated_image: {
          url: "/api/v1/detections/" + id + "/annotated-image",
          media_type: "image/jpeg",
          expires_at: expires,
        },
      });
    }
    if (
      url.pathname.endsWith("original-image") ||
      url.pathname.endsWith("annotated-image")
    ) {
      const source = sources.get(url.pathname.replace("/web-api","").split("/")[4]);
      return route.fulfill({
        contentType: "image/png",
        body: readFileSync(path.join(root, source.scene.name + ".png")),
      });
    }
    if (req.method() === "DELETE") return json({ status: "cancelled" });
    if (req.method() === "POST") {
      const sourceId = req.postDataJSON().source.source_id,
        source = sources.get(sourceId),
        id = "fixture-job-" + sourceId;
      jobs.set(id, { ...source, sourceId });
      return json(
        {
          enrichment_job_id: id,
          status: "queued",
          created_at: new Date().toISOString(),
          expires_at: source.expires,
        },
        202,
      );
    }
    const id = url.pathname.replace("/web-api","").split("/")[4],
      job = jobs.get(id);
    if (url.pathname.endsWith("/results")) {
      const page = Number(url.searchParams.get("page")),
        size = Number(url.searchParams.get("page_size"));
      pages.push(page);
      const items = [...job.scene.results].reverse();
      return json({
        items: items.slice((page - 1) * size, page * size),
        page,
        page_size: size,
        total: items.length,
      });
    }
    return json({
      enrichment_job_id: id,
      status: "completed",
      created_at: new Date().toISOString(),
      expires_at: job.expires,
      source: { kind: "image", source_id: job.sourceId },
      processed_units: job.scene.results.length,
      total_units: job.scene.results.length,
      results_ready: job.scene.results.length,
      progress_percent: 100,
    });
  });
  return pages;
}
export async function chooseScene(page: Page, scene: any) {
  await page
    .getByLabel("Seleccionar imagen", { exact: true })
    .setInputFiles(path.join(root, scene.name + ".png"));
  await page.getByRole("button", { name: "Analizar imagen" }).click();
  await expect(page.locator(".analysis-status strong")).toHaveText(
    /Análisis completo|Resultado parcial/,
  );
}
async function pixels(page: Page, label: string) {
  const image = page.getByRole("img", { name: label, exact: true });
  await expect(image).toBeVisible();
  return image.evaluate((img: HTMLImageElement) => {
    const c = document.createElement("canvas");
    c.width = img.naturalWidth;
    c.height = img.naturalHeight;
    const ctx = c.getContext("2d")!;
    ctx.drawImage(img, 0, 0);
    return {
      width: c.width,
      height: c.height,
      color: [...ctx.getImageData(2, 2, 1, 1).data].slice(0, 3),
    };
  });
}
export async function verifyVehicle(
  page: Page,
  expected: any,
  index: number,
  touch = false,
) {
  const button = page.locator(".detection-list button").nth(index);
  if (touch) await button.tap();
  else await button.click();
  await expect(page.locator(".vehicle-details h3")).toHaveText(
    "Detección " + expected.id,
  );
  await expect(page.locator(".vehicle-details")).toContainText(expected.label);
  expect(await pixels(page, "Recorte del vehículo")).toEqual({
    width: expected.width,
    height: expected.height,
    color: expected.color,
  });
  if (expected.status === "not_detected") {
    await expect(
      page.getByRole("img", { name: "Recorte de la placa", exact: true }),
    ).toHaveCount(0);
    await expect(
      page.getByText("Placa no detectada", { exact: true }),
    ).toBeVisible();
  } else
    expect(await pixels(page, "Recorte de la placa")).toEqual({
      width: expected.plateWidth,
      height: expected.plateHeight,
      color: expected.plateColor,
    });
  if (expected.text)
    await expect(page.getByText(expected.text, { exact: true })).toBeVisible();
  await expect(page.getByText("PRIVATE_CANARY", { exact: true })).toHaveCount(
    0,
  );
}
