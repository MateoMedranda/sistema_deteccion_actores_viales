import { renderHook, act } from "@testing-library/react";
import { it, expect, vi, afterEach } from "vitest";
import { useImageAnalysis } from "../../../src/features/image-analysis/useImageAnalysis";
import {
  detectionResponse,
  expiresAt,
  sourceId,
} from "../../fixtures/imageAnalysis";
afterEach(() => vi.useRealTimers());
it("stops an unfinished cycle by 120 seconds and resumes only explicitly", async () => {
  vi.useFakeTimers();
  const epoch = Date.now();
  vi.spyOn(performance, "now").mockImplementation(() => Date.now() - epoch);
  const accepted = {
    enrichment_job_id: "job",
    status: "queued",
    created_at: new Date().toISOString(),
    expires_at: expiresAt(),
  };
  const client: any = {
    uploadImage: vi.fn().mockResolvedValue(detectionResponse()),
    enrich: vi.fn().mockResolvedValue(accepted),
    annotatedImage: vi.fn().mockResolvedValue(new Blob()),
    originalImage: vi.fn().mockResolvedValue(new Blob()),
    enrichment: vi.fn().mockResolvedValue({
      ...accepted,
      source: { kind: "image", source_id: sourceId },
      processed_units: 0,
      total_units: 2,
      progress_percent: 0,
      results_ready: 0,
    }),
    cancelEnrichment: vi.fn().mockResolvedValue({}),
  };
  const { result, unmount } = renderHook(() => useImageAnalysis(client));
  act(() =>
    result.current.selectFile(new File(["x"], "s.png", { type: "image/png" })),
  );
  act(() => {
    void result.current.analyze();
  });
  await act(async () => {
    await Promise.resolve();
  });
  await act(async () => vi.advanceTimersByTimeAsync(120000));
  expect(result.current.state.phase).toBe("interrupted");
  const calls = client.enrichment.mock.calls.length;
  await act(async () => vi.advanceTimersByTimeAsync(10000));
  expect(client.enrichment).toHaveBeenCalledTimes(calls);
  expect(client.enrich).toHaveBeenCalledTimes(1);
  expect(result.current.state.response?.request_id).toBe(sourceId);
  unmount();
});
