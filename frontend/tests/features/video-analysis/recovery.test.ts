import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, it, expect, vi } from "vitest";
import { useProgressivePlayback } from "../../../src/features/video-analysis/useProgressivePlayback";
import { ApiClient, ClientError } from "../../../src/services/apiClient";
const state = () => ({
  job_id: "a",
  generation: "g",
  revision: 1,
  analysis_state: "analyzing",
  export_state: "waiting",
  frames_processed: 0,
  frames_published: 0,
  available_until_us: 0,
  last_frame_start_us: null,
  media_available: false,
  source: null,
  timeline: {
    timebase: "source-pts",
    width: 64,
    height: 48,
    pixel_to_display: [1, 0, 0, 1, 0, 0],
  },
  buffer_seconds: 5,
  expires_at: new Date(Date.now() + 10000).toISOString(),
  enrichment: { revision: 0 },
});
afterEach(() => vi.useRealTimers());
describe("progressive recovery", () => {
  it("backs off and rechecks the same job without creating another analysis", async () => {
    vi.useFakeTimers();
    const json = vi
      .fn()
      .mockRejectedValueOnce(
        new ClientError(0, { code: "network_unavailable", message: "network" }),
      )
      .mockImplementation(async () => state());
    const client = { json } as unknown as ApiClient;
    const hook = renderHook(() =>
      useProgressivePlayback(client, "a", true, vi.fn()),
    );
    await act(async () => {
      await Promise.resolve();
    });
    expect(json).toHaveBeenCalledTimes(1);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(999);
    });
    expect(json).toHaveBeenCalledTimes(1);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1);
    });
    expect(json).toHaveBeenCalledTimes(2);
    expect(hook.result.current.state?.revision).toBe(1);
    expect(
      json.mock.calls.every((c) => c[0] === "/api/v1/video-jobs/a/playback"),
    ).toBe(true);
  });
  it("withdraws expired UI while its mode is hidden", async () => {
    vi.useFakeTimers();
    const json = vi.fn().mockResolvedValue(state()),
      retire = vi.fn();
    const client = { json } as unknown as ApiClient;
    const hook = renderHook(
      ({ active }) => useProgressivePlayback(client, "a", active, retire),
      { initialProps: { active: true } },
    );
    await act(async () => {
      await Promise.resolve();
    });
    expect(hook.result.current.state).toBeDefined();
    hook.rerender({ active: false });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(10001);
    });
    expect(retire).toHaveBeenCalledTimes(1);
    expect(hook.result.current.state).toBeUndefined();
  });
  it("ignores a status response that arrives after unmount", async () => {
    let finish: (v: unknown) => void = () => {};
    const json = vi.fn(
        () =>
          new Promise((r) => {
            finish = r;
          }),
      ),
      retire = vi.fn();
    const hook = renderHook(() =>
      useProgressivePlayback(
        { json } as unknown as ApiClient,
        "a",
        true,
        retire,
      ),
    );
    hook.unmount();
    await act(async () => {
      finish(state());
      await Promise.resolve();
    });
    expect(retire).not.toHaveBeenCalled();
  });
});
