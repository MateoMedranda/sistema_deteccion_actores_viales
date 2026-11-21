import { renderHook, act } from "@testing-library/react";
import { it, expect, vi } from "vitest";
import { useImageAnalysis } from "../../../src/features/image-analysis/useImageAnalysis";
import {
  detectionResponse,
  vehicleResult,
  expiresAt,
  sourceId,
} from "../../fixtures/imageAnalysis";
it("loads every page and joins 55 vehicles by ID despite shuffled results", async () => {
  const source = detectionResponse();
  source.detections = Array.from({ length: 55 }, (_, i) => ({
    ...source.detections[0],
    detection_id: i + 1,
  }));
  const items = Array.from({ length: 55 }, (_, i) => vehicleResult(55 - i));
  const job = {
    enrichment_job_id: "job",
    status: "completed",
    created_at: new Date().toISOString(),
    expires_at: expiresAt(),
    source: { kind: "image", source_id: sourceId },
    total_units: 55,
    processed_units: 55,
    results_ready: 55,
    progress_percent: 100,
  };
  const client: any = {
    uploadImage: vi.fn().mockResolvedValue(source),
    annotatedImage: vi.fn().mockResolvedValue(new Blob()),
    originalImage: vi.fn().mockResolvedValue(new Blob()),
    enrich: vi.fn().mockResolvedValue(job),
    enrichment: vi.fn().mockResolvedValue(job),
    enrichmentResults: vi.fn(async (_: string, page: number) => ({
      page,
      page_size: 50,
      total: 55,
      items: items.slice((page - 1) * 50, page * 50),
    })),
    cancelEnrichment: vi.fn(),
  };
  const { result, unmount } = renderHook(() => useImageAnalysis(client));
  act(() =>
    result.current.selectFile(new File(["x"], "s.png", { type: "image/png" })),
  );
  await act(async () => result.current.analyze());
  expect(result.current.state.phase).toBe("completed");
  expect(Object.keys(result.current.state.results)).toHaveLength(55);
  for (let i = 1; i <= 55; i++)
    expect(result.current.state.results[i].detection_id).toBe(i);
  expect(client.enrichmentResults.mock.calls.map((c: any) => c[1])).toEqual([
    1, 2,
  ]);
  unmount();
});
