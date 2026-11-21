import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiClient } from "../../src/services/apiClient";
import { detectionResponse } from "../fixtures/imageAnalysis";

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("authenticated image client", () => {
  it("never transmits a key to an external artifact origin", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValue(new Response(new Blob(["image"])));
    vi.stubGlobal("fetch", fetcher);
    const client = new ApiClient("https://service.example", "PRIVATE_TEST_KEY");
    await expect(
      client.blob("https://other.example/image"),
    ).rejects.toMatchObject({ detail: { code: "unsafe_artifact_url" } });
    expect(fetcher).not.toHaveBeenCalled();
  });

  it("rejects a malformed detection response instead of casting it", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(new Response(JSON.stringify({ request_id: "bad" }))),
    );
    await expect(
      new ApiClient("https://service.example", "key").uploadImage(
        new File(["x"], "x.png"),
      ),
    ).rejects.toMatchObject({ detail: { code: "invalid_response" } });
  });

  it("authenticates and validates a canonical response", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify(detectionResponse())));
    vi.stubGlobal("fetch", fetcher);
    const result = await new ApiClient(
      "https://service.example",
      "key",
    ).uploadImage(new File(["x"], "x.png"));
    expect(result.detections[0].detection_id).toBe(1);
    expect(fetcher.mock.calls[0][1].headers["X-API-Key"]).toBe("key");
    expect(fetcher.mock.calls[0][1].redirect).toBe("error");
  });

  it("aborts a blocked detection at its deadline without retry", async () => {
    vi.useFakeTimers();
    const fetcher = vi.fn(
      (_url: string, init: RequestInit) =>
        new Promise<Response>((_resolve, reject) => {
          init.signal?.addEventListener("abort", () =>
            reject(new DOMException("Aborted", "AbortError")),
          );
        }),
    );
    vi.stubGlobal("fetch", fetcher);
    const outcome = new ApiClient("https://service.example", "key")
      .uploadImage(new File(["x"], "x.png"))
      .catch((e) => e);
    await vi.advanceTimersByTimeAsync(120_001);
    expect(await outcome).toMatchObject({
      detail: { code: "request_timeout" },
    });
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("does not display a private server error message", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            code: "model_unavailable",
            message: "PRIVATE_PATH_AND_SECRET",
          }),
          { status: 503 },
        ),
      ),
    );
    const outcome = await new ApiClient("https://service.example", "key")
      .uploadImage(new File(["x"], "x.png"))
      .catch((e) => e);
    expect(outcome.message).not.toContain("PRIVATE_PATH");
  });
});
