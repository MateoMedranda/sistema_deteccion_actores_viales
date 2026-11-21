import type { Page } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";
import {
  detectionResponse,
  vehicleResult,
  expiresAt,
  sourceId,
} from "../tests/fixtures/imageAnalysis";
export async function mockScenario(page: Page, scenario: string) {
  const image = readFileSync(path.resolve("e2e/fixtures/canonical.png"));
  const accepted = {
    enrichment_job_id: "synthetic-job",
    status: "queued",
    created_at: new Date().toISOString(),
    expires_at: expiresAt(),
  };
  await page.route("http://127.0.0.1:8767/api/**", async (route) => {
    const request = route.request(),
      url = new URL(request.url());
    const json = (body: unknown, status = 200) =>
      route.fulfill({ status, json: body });
    if (url.pathname.endsWith("/images")) {
      if (scenario === "detecting")
        await new Promise((r) => setTimeout(r, 2500));
      if (scenario === "error") return json({ code: "model_unavailable" }, 503);
      const source = detectionResponse();
      if (scenario === "empty") source.detections = [];
      if (scenario === "expired")
        source.source_expires_at = new Date(Date.now() + 250).toISOString();
      return json(source);
    }
    if (
      url.pathname.endsWith("original-image") ||
      url.pathname.endsWith("annotated-image")
    )
      return route.fulfill({ contentType: "image/png", body: image });
    if (request.method() === "DELETE") return json({ status: "cancelled" });
    if (request.method() === "POST") return json(accepted, 202);
    if (url.pathname.endsWith("/results")) {
      const items = [
        vehicleResult(),
        { ...vehicleResult(2), class_id: 1, class_name: "truck" },
      ];
      if (scenario === "partial") {
        items[0].attributes_status = "failed";
        items[0].attributes = [];
        items[0].plate.status = items[0].plate_status = "failed";
        items[0].plate.text = null as any;
      }
      return json({ items, page: 1, page_size: 50, total: 2 });
    }
    if (scenario === "interrupted") return route.abort("failed");
    return json({
      ...accepted,
      status:
        scenario === "enriching"
          ? "processing"
          : scenario === "cancelled"
            ? "cancelled"
            : "completed",
      source: { kind: "image", source_id: sourceId },
      progress_percent: scenario === "enriching" ? 50 : 100,
      processed_units: scenario === "enriching" ? 1 : 2,
      total_units: 2,
      results_ready: scenario === "enriching" ? 0 : 2,
    });
  });
}
