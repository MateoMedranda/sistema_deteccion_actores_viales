import { it, expect, vi, afterEach } from "vitest";
import { ApiClient } from "../../src/services/apiClient";
afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});
function blocked() {
  const spy = vi.fn(
    (_url: unknown, init: RequestInit) =>
      new Promise<Response>((_, reject) =>
        init.signal!.addEventListener("abort", () =>
          reject(new DOMException("Aborted", "AbortError")),
        ),
      ),
  );
  vi.stubGlobal("fetch", spy);
  return spy;
}
it.each([
  ["create", 15000],
  ["status", 10000],
  ["evidence", 30000],
] as const)("%s has an individual timeout", async (kind, ms) => {
  vi.useFakeTimers();
  blocked();
  const client = new ApiClient("http://localhost:8000", "key");
  const promise =
    kind === "create"
      ? client.enrich("image", "source")
      : kind === "status"
        ? client.enrichment("job", { timeoutMs: 10000 })
        : client.originalImage("/original");
  const assertion = expect(promise).rejects.toMatchObject({
    detail: { code: "request_timeout" },
  });
  await vi.advanceTimersByTimeAsync(ms);
  await assertion;
});
it("uses source expiry before the request deadline", async () => {
  vi.useFakeTimers();
  blocked();
  const client = new ApiClient("http://localhost:8000", "key");
  const promise = client.enrichment("job", {
    timeoutMs: 10000,
    expiresAt: Date.now() + 50,
  });
  const assertion = expect(promise).rejects.toMatchObject({
    detail: { code: "request_timeout" },
  });
  await vi.advanceTimersByTimeAsync(51);
  await assertion;
});
it("keeps timeout active while response bytes are still loading", async () => {
  vi.useFakeTimers();
  vi.stubGlobal(
    "fetch",
    vi.fn(async (_: unknown, init: RequestInit) => ({
      ok: true,
      blob: () =>
        new Promise((_, reject) =>
          init.signal!.addEventListener("abort", () =>
            reject(new DOMException("Aborted", "AbortError")),
          ),
        ),
    })),
  );
  const client = new ApiClient("http://localhost:8000", "key");
  const promise = client.originalImage("/original", { timeoutMs: 20 });
  const assertion = expect(promise).rejects.toMatchObject({
    detail: { code: "request_timeout" },
  });
  await vi.advanceTimersByTimeAsync(21);
  await assertion;
});

it.each([401, 404, 410])(
  "preserves HTTP %s without awaiting a blocked error body",
  async (status) => {
    const json = vi.fn(() => new Promise(() => {}));
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({ ok: false, status, json })),
    );
    const client = new ApiClient("http://localhost:8000", "key");
    await expect(
      client.enrichment("job", { timeoutMs: 20 }),
    ).rejects.toMatchObject({ status });
    expect(json).not.toHaveBeenCalled();
    expect((vi.mocked(fetch).mock.calls[0][1] as RequestInit).signal?.aborted).toBe(true);
  },
);
