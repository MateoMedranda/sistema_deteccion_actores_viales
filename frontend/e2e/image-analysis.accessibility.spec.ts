import { test, expect } from "@playwright/test";
import { complete } from "./helpers";
test("keyboard, touch alternatives, enlarged text and reduced motion", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await complete(page);
  for (const button of await page.locator(".detection-list button").all()) {
    const box = await button.boundingBox();
    expect(box!.height).toBeGreaterThanOrEqual(44);
    expect(box!.width).toBeGreaterThanOrEqual(44);
  }
  await page.addStyleTag({ content: "html{font-size:200%}" });
  const overflow = await page.evaluate(() =>
    [...document.querySelectorAll("main *")]
      .filter(
        (e) =>
          e.checkVisibility() &&
          e.getBoundingClientRect().right > innerWidth + 1,
      )
      .map((e) => ({
        tag: e.tagName,
        cls: e.className,
        width: e.getBoundingClientRect().width,
      })),
  );
  expect(overflow).toEqual([]);
  await page.getByRole("button", { name: "Cerrar ficha del vehículo" }).click();
  await expect(page.getByText("Explora cada vehículo")).toBeVisible();
  await page.locator(".detection-list button").first().focus();
  await page.keyboard.press("Enter");
  await expect(page.locator(".detection-list button").first()).toBeFocused();
  expect(
    await page
      .locator(".image-workspace")
      .evaluate((el) => getComputedStyle(el).backgroundImage),
  ).toBe("none");
});

test("computed text and control colors meet selected contrast thresholds", async ({
  page,
}) => {
  await complete(page);
  const colors = await page.evaluate(() => {
    const selectors = [
      ".workspace-heading h2",
      ".workspace-heading p",
      ".vehicle-details h3",
      ".privacy-note",
      ".detection-list small",
    ];
    return selectors.map((selector) => {
      const el = document.querySelector(selector)!;
      let parent: Element | null = el;
      let bg = "rgba(0, 0, 0, 0)";
      while (parent && bg === "rgba(0, 0, 0, 0)") {
        bg = getComputedStyle(parent).backgroundColor;
        parent = parent.parentElement;
      }
      return { selector, color: getComputedStyle(el).color, bg };
    });
  });
  const luminance = (color: string) => {
    const channels = color
      .match(/[\d.]+/g)!
      .slice(0, 3)
      .map(Number)
      .map((v) => {
        const s = v / 255;
        return s <= 0.04045 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
      });
    return channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722;
  };
  for (const pair of colors) {
    const a = luminance(pair.color),
      b = luminance(pair.bg);
    expect(
      (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05),
      pair.selector,
    ).toBeGreaterThanOrEqual(4.5);
  }
  expect(
    (luminance("rgb(255,255,255)") + 0.05) /
      (luminance("rgb(40,85,166)") + 0.05),
  ).toBeGreaterThanOrEqual(3);
});
