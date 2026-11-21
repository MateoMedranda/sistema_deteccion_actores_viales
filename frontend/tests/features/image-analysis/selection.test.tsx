import { render, screen, fireEvent } from "@testing-library/react";
import { it, expect, vi } from "vitest";
import { DetectionList } from "../../../src/features/image-analysis/DetectionList";
import { detectionResponse } from "../../fixtures/imageAnalysis";
it("offers equivalent controls for each eligible detection", () => {
  const select = vi.fn();
  render(
    <DetectionList
      source={detectionResponse() as any}
      selected={1}
      onSelect={select}
    />,
  );
  const buttons = screen.getAllByRole("button");
  expect(buttons).toHaveLength(2);
  expect(buttons[0]).toHaveAttribute("aria-pressed", "true");
  fireEvent.click(buttons[1]);
  expect(select).toHaveBeenCalledWith(2);
  expect(buttons[1]).toHaveAttribute("aria-controls", "vehicle-details");
});
