import { render, screen, waitFor } from "@testing-library/react";
import { it, expect, vi } from "vitest";
import { EvidenceCrop } from "../../../src/features/image-analysis/EvidenceCrop";
vi.mock("../../../src/utils/imageGeometry", () => ({
  extractCrop: vi.fn(async () => new Blob(["pixels"], { type: "image/png" })),
}));
it("revokes the selected crop on identity change and unmount", async () => {
  let count = 0;
  vi.spyOn(URL, "createObjectURL").mockImplementation(
    () => "blob:crop-" + ++count,
  );
  const revoke = vi.spyOn(URL, "revokeObjectURL");
  const box = { x_min: 0, y_min: 0, x_max: 5, y_max: 5 };
  const { rerender, unmount } = render(
    <EvidenceCrop
      original="blob:original"
      box={box}
      label="Crop"
      identity="source:1"
    />,
  );
  await waitFor(() =>
    expect(screen.getByRole("img")).toHaveAttribute("src", "blob:crop-1"),
  );
  rerender(
    <EvidenceCrop
      original="blob:original"
      box={box}
      label="Crop"
      identity="source:2"
    />,
  );
  await waitFor(() =>
    expect(screen.getByRole("img")).toHaveAttribute("src", "blob:crop-2"),
  );
  expect(revoke).toHaveBeenCalledWith("blob:crop-1");
  unmount();
  expect(revoke).toHaveBeenCalledWith("blob:crop-2");
});
