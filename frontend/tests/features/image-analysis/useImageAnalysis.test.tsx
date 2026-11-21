import { renderHook, act, waitFor } from "@testing-library/react";
import { it, expect, vi } from "vitest";
import { useImageAnalysis } from "../../../src/features/image-analysis/useImageAnalysis";
import {
  detectionResponse,
  vehicleResult,
  expiresAt,
  sourceId,
} from "../../fixtures/imageAnalysis";
it("one action detects, enriches and joins completed results without duplicate POST", async () => {
  const accepted = {
    enrichment_job_id: "job1",
    status: "queued",
    created_at: new Date().toISOString(),
    expires_at: expiresAt(),
  };
  const client: any = {
    uploadImage: vi.fn().mockResolvedValue(detectionResponse()),
    annotatedImage: vi.fn().mockResolvedValue(new Blob()),
    originalImage: vi.fn().mockResolvedValue(new Blob()),
    enrich: vi.fn().mockResolvedValue(accepted),
    enrichment: vi.fn().mockResolvedValue({
      ...accepted,
      status: "completed",
      source: { kind: "image", source_id: sourceId },
      total_units: 2,
      processed_units: 2,
      results_ready: 2,
      progress_percent: 100,
    }),
    enrichmentResults: vi.fn().mockResolvedValue({
      page: 1,
      page_size: 50,
      total: 2,
      items: [
        { ...vehicleResult(2), class_id: 1, class_name: "truck" },
        vehicleResult(1),
      ],
    }),
    cancelEnrichment: vi.fn().mockResolvedValue({}),
  };
  const { result, unmount } = renderHook(() => useImageAnalysis(client));
  act(() =>
    result.current.selectFile(
      new File(["pixels"], "scene.png", { type: "image/png" }),
    ),
  );
  act(() => {
    void result.current.analyze();
    void result.current.analyze();
  });
  await waitFor(() => expect(result.current.state.phase).toBe("completed"));
  expect(client.uploadImage).toHaveBeenCalledTimes(1);
  expect(client.enrich).toHaveBeenCalledTimes(1);
  expect(result.current.state.results[1].detection_id).toBe(1);
  unmount();
});
