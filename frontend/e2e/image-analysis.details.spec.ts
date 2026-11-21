import { test, expect } from "@playwright/test";
import { complete } from "./helpers";
test("vehicle and plate crops use exact canonical pixel sizes", async ({
  page,
}) => {
  await complete(page);
  for (const button of await page.locator(".detection-list button").all()) {
    await button.click();
    await expect(
      page.getByRole("img", { name: "Recorte de la placa", exact: true }),
    ).toBeVisible();
    const sizes = await page
      .getByRole("img", { name: "Recorte del vehículo", exact: true })
      .evaluate((img: HTMLImageElement) => ({
        width: img.naturalWidth,
        height: img.naturalHeight,
      }));
    expect(sizes.width).toBeGreaterThan(0);
    expect(sizes.height).toBeGreaterThan(0);
  }
  await expect(page.getByText("Track ID")).toHaveCount(0);
});

test("crop pixels equal the corresponding original region", async ({
  page,
}) => {
  await complete(page);
  const pixels = await page.evaluate(async () => {
    const crop = document.querySelector(
      'img[alt="Recorte del veh\u00edculo"]',
    ) as HTMLImageElement;
    const figure = crop.closest("figure")!;
    const canvas = document.createElement("canvas");
    canvas.width = crop.naturalWidth;
    canvas.height = crop.naturalHeight;
    const ctx = canvas.getContext("2d")!;
    ctx.drawImage(crop, 0, 0);
    return {
      width: canvas.width,
      height: canvas.height,
      pixel: [...ctx.getImageData(10, 10, 1, 1).data],
      visible: figure.checkVisibility(),
    };
  });
  expect(pixels.width).toBe(275);
  expect(pixels.height).toBe(280);
  expect(pixels.pixel.slice(0, 3)).toEqual([40, 73, 92]);
  expect(pixels.visible).toBe(true);
});
