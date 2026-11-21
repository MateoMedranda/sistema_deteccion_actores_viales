import { renderHook, act } from "@testing-library/react";
import { it, expect, vi } from "vitest";
import { useImageAnalysis } from "../../../src/features/image-analysis/useImageAnalysis";
import {
  detectionResponse,
  expiresAt,
  sourceId,
} from "../../fixtures/imageAnalysis";
it("a failed original has a terminal error and can retry without inference", async () => {
  const source = detectionResponse();
  source.detections = [];
  const client: any = {
    uploadImage: vi.fn().mockResolvedValue(source),
    annotatedImage: vi.fn(),
    originalImage: vi.fn().mockRejectedValueOnce(new Error("offline")).mockResolvedValue(new Blob()),
  };
  const { result, unmount } = renderHook(() => useImageAnalysis(client));
  act(() =>
    result.current.selectFile(
      new File(["x"], "scene.png", { type: "image/png" }),
    ),
  );
  await act(async () => result.current.analyze());
  expect(result.current.state.originalState).toBe("failed");
  expect(client.annotatedImage).not.toHaveBeenCalled();
  await act(async () => result.current.retryMedia("original"));
  expect(result.current.state.originalState).toBe("ready");
  expect(client.annotatedImage).not.toHaveBeenCalled();
  expect(client.uploadImage).toHaveBeenCalledTimes(1);
  unmount();
});
