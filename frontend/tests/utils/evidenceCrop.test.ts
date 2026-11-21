import { it, expect } from "vitest";
import { plateCrop, vehicleCrop } from "../../src/utils/imageGeometry";
it("clamps without manufacturing a pixel", () => {
  expect(
    vehicleCrop({ x_min: -3.1, y_min: 1.9, x_max: 100, y_max: 21 }, 20, 20),
  ).toEqual({ x_min: 0, y_min: 1, x_max: 20, y_max: 20 });
  expect(
    plateCrop(
      { x_min: 0, y_min: 0, x_max: 2, y_max: 2 },
      { x_min: 0.01, y_min: 0.01, x_max: 0.02, y_max: 0.02 },
    ),
  ).toBeUndefined();
});
it("rejects absent, reversed and nonfinite relative boxes", () => {
  const v = { x_min: 0, y_min: 0, x_max: 20, y_max: 20 };
  expect(plateCrop(v)).toBeUndefined();
  expect(
    plateCrop(v, { x_min: 0.8, y_min: 0, x_max: 0.2, y_max: 1 }),
  ).toBeUndefined();
  expect(
    plateCrop(v, { x_min: NaN, y_min: 0, x_max: 1, y_max: 1 }),
  ).toBeUndefined();
});

it("restores integer coordinates after normalized IEEE roundoff", () => {
  expect(
    plateCrop(
      { x_min: 0, y_min: 0, x_max: 22, y_max: 22 },
      { x_min: 15 / 22, y_min: 0, x_max: 1, y_max: 1 },
    )?.x_min,
  ).toBe(15);
});
