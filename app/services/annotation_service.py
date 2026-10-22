from __future__ import annotations

import cv2
import numpy as np

from app.domain.models import Detection


def annotate(image: np.ndarray, detections: list[Detection]) -> bytes:
    canvas = image.copy()
    for detection in detections:
        color = (0, 200, 0)
        cv2.rectangle(canvas, (detection.x_min, detection.y_min), (detection.x_max, detection.y_max), color, 2)
        label = f"{detection.class_name} {detection.confidence:.2f}"
        cv2.putText(
            canvas,
            label,
            (detection.x_min, max(20, detection.y_min - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
            cv2.LINE_AA,
        )
    ok, encoded = cv2.imencode(".jpg", canvas)
    if not ok:
        raise RuntimeError("Could not encode annotated image")
    return encoded.tobytes()
