import { render, screen } from "@testing-library/react";
import { it, expect } from "vitest";
import { ImageUpload } from "../../../src/features/image-analysis/ImageUpload";
it.each([
  [2, 3],
  [5, 9],
])("shows server-configured limits %s MiB and %s MP", (mib, mp) => {
  render(
    <ImageUpload
      policy={{
        media_types: ["image/jpeg", "image/png"],
        max_upload_bytes: mib * 1024 * 1024,
        max_image_pixels: mp * 1000000,
      }}
      disabled={false}
      generation={0}
      preview=""
      onChoose={() => {}}
      onAnalyze={() => {}}
      onReset={() => {}}
    />,
  );
  expect(
    screen.getByText(new RegExp(mib + " MiB.*" + mp + " MP")),
  ).toBeVisible();
});
