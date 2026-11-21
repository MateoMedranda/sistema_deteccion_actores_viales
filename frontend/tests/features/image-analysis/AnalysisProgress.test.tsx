import { render, screen } from "@testing-library/react";
import { it, expect } from "vitest";
import { AnalysisProgress } from "../../../src/features/image-analysis/AnalysisProgress";
import { initialState } from "../../../src/features/image-analysis/imageAnalysisReducer";
it.each([
  ["submitting", "Enviando enriquecimiento"],
  ["queued", "En cola"],
  ["processing", "Procesando vehículos"],
] as const)("announces %s independently", (enrichmentStage, label) => {
  render(
    <AnalysisProgress
      state={{
        ...initialState,
        phase: "enriching",
        enrichmentStage,
        jobId: enrichmentStage === "submitting" ? undefined : "job",
        progress: 0,
      }}
    />,
  );
  expect(screen.getByText(label)).toBeVisible();
  expect(screen.queryByText("0%")).toBe(
    enrichmentStage === "submitting" ? null : screen.getByText("0%"),
  );
});
