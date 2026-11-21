import { render, screen } from "@testing-library/react";
import { it, expect } from "vitest";
import { VehicleDetails } from "../../../src/features/image-analysis/VehicleDetails";
import { detectionResponse, vehicleResult } from "../../fixtures/imageAnalysis";
it("keeps localization but never displays unreadable canary text", () => {
  const d = detectionResponse().detections[0],
    r: any = vehicleResult();
  r.plate.status = r.plate_status = "unreadable";
  r.plate.text = "PRIVATE_CANARY";
  render(
    <VehicleDetails
      sourceId="s"
      detection={d}
      result={r}
      original=""
      pending={false}
      onClose={() => {}}
    />,
  );
  expect(screen.getByText("Placa ilegible")).toBeVisible();
  expect(screen.queryByText("PRIVATE_CANARY")).toBeNull();
  expect(screen.getByText("Recorte de la placa")).toBeVisible();
});
