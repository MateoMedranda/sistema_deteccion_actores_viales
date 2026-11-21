export const sourceId = "00000000-0000-4000-8000-000000000001";
export const expiresAt = () => new Date(Date.now() + 300_000).toISOString();
export const detectionResponse = () => ({
  request_id: sourceId,
  status: "completed",
  processing_time_ms: 45,
  image: { width: 640, height: 400, media_type: "image/png" },
  detections: [
    {
      detection_id: 1,
      class_id: 0,
      class_name: "car",
      confidence: 0.96,
      bbox: { x_min: 20, y_min: 25, x_max: 290, y_max: 300 },
      enrichment_eligible: true,
    },
    {
      detection_id: 2,
      class_id: 1,
      class_name: "truck",
      confidence: 0.91,
      bbox: { x_min: 340, y_min: 45, x_max: 610, y_max: 330 },
      enrichment_eligible: true,
    },
  ],
  source_expires_at: expiresAt(),
  original_image: {
    url: "/api/v1/detections/" + sourceId + "/original-image",
    media_type: "image/png",
    expires_at: expiresAt(),
  },
  annotated_image: {
    url: "/api/v1/detections/" + sourceId + "/annotated-image",
    media_type: "image/jpeg",
    expires_at: expiresAt(),
  },
});
export const vehicleResult = (id = 1) => ({
  vehicle_key: "detection-" + id,
  detection_id: id,
  track_id: null,
  class_id: 0,
  class_name: "car",
  evidence_frame_indexes: [],
  attributes_status: "completed",
  plate_status: "read",
  attributes: [{ name: "color", label: "white", confidence: 0.93 }],
  plate: {
    status: "read",
    text: "SYN123",
    used_enhancement: false,
    evidence_frame_indexes: [],
    bbox_relative: { x_min: 0.1, y_min: 0.65, x_max: 0.4, y_max: 0.8 },
    localizer_confidence: 0.95,
    ocr_confidence: 0.92,
  },
  error_code: null,
});

export const manyDetections = (count = 55) => {
  const source = detectionResponse();
  source.detections = Array.from({ length: count }, (_, index) => ({
    ...source.detections[0],
    detection_id: index + 1,
  }));
  return source;
};
export const plateVariants = () =>
  (["read", "unreadable", "not_detected", "failed"] as const).map(
    (status, index) => {
      const item = vehicleResult(index + 1);
      return {
        ...item,
        plate_status: status,
        plate: {
          ...item.plate,
          status,
          text: status === "read" ? "SYN123" : "PRIVATE_CANARY",
        },
      };
    },
  );
export const overlappingDetections = () => {
  const source = detectionResponse();
  source.detections[1] = {
    ...source.detections[1],
    bbox: { ...source.detections[0].bbox },
  };
  return source;
};
