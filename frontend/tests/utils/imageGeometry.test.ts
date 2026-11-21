import { describe, it, expect } from "vitest";
import {
  projectBox,
  vehicleCrop,
  plateCrop,
} from "../../src/utils/imageGeometry";
describe("canonical geometry", () => {
  it("projects independent of viewport", () => {
    expect(
      projectBox({ x_min: 10, y_min: 20, x_max: 50, y_max: 80 }, 100, 200),
    ).toEqual({ left: "10%", top: "10%", width: "40%", height: "30%" });
  });
  it("rejects degenerate boxes", () => {
    expect(
      vehicleCrop({ x_min: 3, y_min: 4, x_max: 3, y_max: 9 }, 20, 20),
    ).toBeUndefined();
  });
  it("uses plate coordinates within vehicle", () => {
    expect(
      plateCrop(
        { x_min: 100, y_min: 50, x_max: 300, y_max: 150 },
        { x_min: 0.1, y_min: 0.5, x_max: 0.5, y_max: 0.9 },
      ),
    ).toEqual({ x_min: 120, y_min: 100, x_max: 200, y_max: 140 });
  });
});
