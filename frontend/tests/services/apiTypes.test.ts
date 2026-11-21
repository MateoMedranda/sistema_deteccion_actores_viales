import { it, expect } from "vitest";
import {
  parseDetectionResponse,
  parseEnrichmentPage,
} from "../../src/services/apiTypes";
import { detectionResponse, vehicleResult } from "../fixtures/imageAnalysis";
it("rejects duplicate IDs, nonfinite confidences and reversed geometry", () => {
  const source = detectionResponse();
  source.detections.push(source.detections[0]);
  expect(() => parseDetectionResponse(source)).toThrow();
  const invalid = detectionResponse();
  invalid.detections[0].bbox.x_max = 0;
  expect(() => parseDetectionResponse(invalid)).toThrow();
  const confidence = detectionResponse();
  confidence.detections[0].confidence = NaN;
  expect(() => parseDetectionResponse(confidence)).toThrow();
});
it.each(["unreadable", "not_detected", "failed"])(
  "drops any canary text when plate status is %s",
  (status) => {
    const item: any = vehicleResult();
    item.plate.status = item.plate_status = status;
    item.plate.text = "PRIVATE_CANARY";
    const page = parseEnrichmentPage({
      page: 1,
      page_size: 50,
      total: 1,
      items: [item],
    });
    expect(JSON.stringify(page)).not.toContain("PRIVATE_CANARY");
  },
);
