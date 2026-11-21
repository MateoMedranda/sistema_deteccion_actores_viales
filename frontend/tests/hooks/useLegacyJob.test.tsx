import { renderHook, act } from "@testing-library/react";
import { it, expect, vi } from "vitest";
import { useLegacyJob } from "../../src/hooks/useLegacyJob";
it("cancels a legacy job whose POST resolves after unmount", async () => {
  let resolve!: (v: any) => void;
  const promise = new Promise((r) => (resolve = r)),
    cancel = vi.fn().mockResolvedValue({});
  const { result, unmount } = renderHook(() =>
    useLegacyJob({ poll: vi.fn(), cancel, idKey: "job_id" }),
  );
  act(() => {
    void result.current.run(() => promise);
  });
  unmount();
  await act(async () => resolve({ job_id: "late", status: "queued" }));
  expect(cancel).toHaveBeenCalledWith("late");
});

it("removes completed count data at expiry without another request", async () => {
  vi.useFakeTimers();
  const poll = vi.fn(),
    cancel = vi.fn();
  const { result, unmount } = renderHook(() =>
    useLegacyJob({ poll, cancel, idKey: "count_job_id" }),
  );
  await act(async () =>
    result.current.run(async () => ({
      count_job_id: "count",
      status: "completed",
      summary: [{ total: 1 }],
      expires_at: new Date(Date.now() + 50).toISOString(),
    })),
  );
  await act(async () => vi.advanceTimersByTimeAsync(51));
  expect(result.current.job).toBeUndefined();
  expect(poll).not.toHaveBeenCalled();
  unmount();
  vi.useRealTimers();
});

it("aborts a suspended create on unmount even when remote cancellation fails", async () => {
  let signal: AbortSignal | undefined;
  const cancel = vi.fn().mockRejectedValue(new Error("offline"));
  const { result, unmount } = renderHook(() =>
    useLegacyJob({ poll: vi.fn(), cancel, idKey: "job_id" }),
  );
  act(() => {
    void result.current.run((options) => {
      signal = options.signal;
      return new Promise(() => {});
    });
  });
  unmount();
  expect(signal?.aborted).toBe(true);
});
