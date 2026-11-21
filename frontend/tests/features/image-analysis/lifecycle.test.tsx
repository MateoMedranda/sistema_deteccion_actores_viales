import { renderHook, act, waitFor } from "@testing-library/react";
import { it, expect, vi, afterEach } from "vitest";
import { useImageAnalysis } from "../../../src/features/image-analysis/useImageAnalysis";
import {
  detectionResponse,
  vehicleResult,
  expiresAt,
  sourceId,
} from "../../fixtures/imageAnalysis";
import { ClientError } from "../../../src/services/apiClient";
const file = () => new File(["x"], "scene.png", { type: "image/png" });
function deferred<T>() {
  let resolve!: (v: T) => void;
  const promise = new Promise<T>((r) => (resolve = r));
  return { promise, resolve };
}
function api() {
  const accepted = {
    enrichment_job_id: "j1",
    status: "queued",
    created_at: new Date().toISOString(),
    expires_at: expiresAt(),
  };
  return {
    accepted,
    client: {
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
          vehicleResult(1),
          { ...vehicleResult(2), class_id: 1, class_name: "truck" },
        ],
      }),
      cancelEnrichment: vi.fn().mockResolvedValue({}),
    },
  };
}
afterEach(() => vi.useRealTimers());
it("late detection cannot restore a discarded image", async () => {
  const { client } = api(),
    late = deferred<any>();
  client.uploadImage.mockReturnValue(late.promise);
  const { result, unmount } = renderHook(() => useImageAnalysis(client as any));
  act(() => result.current.selectFile(file()));
  act(() => {
    void result.current.analyze();
  });
  act(() => result.current.reset());
  await act(async () => late.resolve(detectionResponse()));
  expect(result.current.state.response).toBeUndefined();
  expect(client.enrich).not.toHaveBeenCalled();
  unmount();
});
it("late accepted job is cancelled even when creation completed after reset", async () => {
  const { client, accepted } = api(),
    late = deferred<any>();
  client.enrich.mockReturnValue(late.promise);
  const { result, unmount } = renderHook(() => useImageAnalysis(client as any));
  act(() => result.current.selectFile(file()));
  act(() => {
    void result.current.analyze();
  });
  await waitFor(() => expect(client.enrich).toHaveBeenCalled());
  act(() => result.current.reset());
  await act(async () => late.resolve(accepted));
  expect(client.cancelEnrichment).toHaveBeenCalledWith("j1", expect.anything());
  expect(result.current.state.jobId).toBeUndefined();
  unmount();
});
it("no eligible actor does not submit enrichment", async () => {
  const { client } = api();
  const source = detectionResponse();
  source.detections = [];
  client.uploadImage.mockResolvedValue(source);
  const { result, unmount } = renderHook(() => useImageAnalysis(client as any));
  act(() => result.current.selectFile(file()));
  await act(async () => result.current.analyze());
  expect(result.current.state.phase).toBe("empty");
  expect(client.enrich).not.toHaveBeenCalled();
  unmount();
});
it("resume observes same job without POSTing again", async () => {
  const { client } = api();
  client.enrichment.mockRejectedValueOnce(
    new ClientError(0, { code: "request_timeout", message: "safe" }),
  );
  const { result, unmount } = renderHook(() => useImageAnalysis(client as any));
  act(() => result.current.selectFile(file()));
  await act(async () => result.current.analyze());
  expect(result.current.state.phase).toBe("interrupted");
  await act(async () => result.current.resume());
  expect(result.current.state.phase).toBe("completed");
  expect(client.enrich).toHaveBeenCalledTimes(1);
  unmount();
});
it("expiry removes all local evidence independently of polling", async () => {
  vi.useFakeTimers();
  const { client } = api(),
    source = detectionResponse();
  source.source_expires_at = new Date(Date.now() + 100).toISOString();
  client.uploadImage.mockResolvedValue(source);
  const { result, unmount } = renderHook(() => useImageAnalysis(client as any));
  act(() => result.current.selectFile(file()));
  await act(async () => result.current.analyze());
  await act(async () => vi.advanceTimersByTimeAsync(101));
  expect(result.current.state.phase).toBe("expired");
  expect(result.current.state.original).toBe("");
  expect(result.current.state.file).toBeUndefined();
  expect(result.current.state.results).toEqual({});
  unmount();
});
it("rejects result association with a different class", async () => {
  const { client } = api();
  client.enrichmentResults.mockResolvedValue({
    page: 1,
    page_size: 50,
    total: 1,
    items: [{ ...vehicleResult(), class_id: 99 }],
  });
  const { result, unmount } = renderHook(() => useImageAnalysis(client as any));
  act(() => result.current.selectFile(file()));
  await act(async () => result.current.analyze());
  expect(result.current.state.results).toEqual({});
  expect(result.current.state.phase).toBe("interrupted");
  unmount();
});

it.each(["originalImage"] as const)(
  "withdraws access denial without waiting for other asset: %s",
  async (denied) => {
    const { client } = api();
    const other = "enrichmentResults";
    const pending = deferred<Blob>();
    client[other].mockReturnValue(pending.promise);
    client[denied].mockRejectedValue(
      new ClientError(401, { code: "invalid_api_key", message: "safe" }),
    );
    const { result, unmount } = renderHook(() =>
      useImageAnalysis(client as any),
    );
    act(() => result.current.selectFile(file()));
    await act(async () => result.current.analyze());
    expect(result.current.state.response).toBeUndefined();
    expect(result.current.state.original).toBe("");
    await act(async () => pending.resolve(new Blob()));
    expect(result.current.state.response).toBeUndefined();
    unmount();
  },
);

it("does not offer an old terminal ID after ambiguous retry creation", async () => {
  const { client, accepted } = api();
  client.enrichment.mockResolvedValue({
    ...accepted,
    status: "failed",
    source: { kind: "image", source_id: sourceId },
    total_units: 2,
    processed_units: 0,
    progress_percent: 0,
    results_ready: 0,
  });
  const { result, unmount } = renderHook(() => useImageAnalysis(client as any));
  act(() => result.current.selectFile(file()));
  await act(async () => result.current.analyze());
  client.enrich.mockRejectedValue(
    new ClientError(0, { code: "request_timeout", message: "safe" }),
  );
  await act(async () => result.current.retryEnrichment());
  expect(result.current.state.jobId).toBeUndefined();
  expect(result.current.state.phase).toBe("failed");
  expect(result.current.state.message).toMatch(/confirmar/);
  const calls = client.enrichment.mock.calls.length;
  await act(async () => result.current.resume());
  expect(client.enrichment).toHaveBeenCalledTimes(calls);
  expect(client.uploadImage).toHaveBeenCalledTimes(1);
  unmount();
});

it("explains an ambiguous first creation even before React commits the detected state",async()=>{const {client}=api();client.enrich.mockRejectedValue(new ClientError(0,{code:"network_unavailable",message:"safe"}));const {result,unmount}=renderHook(()=>useImageAnalysis(client as any));act(()=>result.current.selectFile(file()));await act(async()=>result.current.analyze());expect(result.current.state.message).toMatch(/confirmar/);expect(result.current.state.jobId).toBeUndefined();expect(client.enrich).toHaveBeenCalledTimes(1);unmount();});
