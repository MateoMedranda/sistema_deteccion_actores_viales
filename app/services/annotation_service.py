from __future__ import annotations

import cv2
import numpy as np

from app.domain.models import Detection


# BGR palette with enough contrast on road scenes. The class id makes the color stable
# for images, videos and future UI legends without relying on model class names.
_CLASS_COLORS: tuple[tuple[int, int, int], ...] = (
    (255, 99, 71),   # blue-ish red in BGR display order is handled by OpenCV
    (60, 200, 80),
    (255, 170, 40),
    (190, 80, 220),
    (60, 210, 210),
    (220, 130, 40),
    (150, 80, 255),
    (80, 180, 255),
)


def color_for_class(class_id: int) -> tuple[int, int, int]:
    """Return a stable high-contrast BGR color for a detected class."""
    return _CLASS_COLORS[class_id % len(_CLASS_COLORS)]


def annotate(image: np.ndarray, detections: list[Detection]) -> bytes:
    canvas = image.copy()
    thickness = max(1, round(min(image.shape[:2]) / 500))
    for detection in detections:
        color = color_for_class(detection.class_id)
        cv2.rectangle(canvas, (detection.x_min, detection.y_min), (detection.x_max, detection.y_max), color, thickness, cv2.LINE_AA)
        label = f"{detection.class_name} {detection.confidence:.0%}"
        (label_width, label_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.32, 1)
        # Prefer the small label above the box; use the top interior only when it would leave the image.
        label_bottom = detection.y_min - 4
        if label_bottom - label_height - baseline < 0:
            label_bottom = min(image.shape[0] - baseline - 2, detection.y_min + label_height + baseline + 4)
        label_left = max(0, min(detection.x_min, image.shape[1] - label_width - 4))
        cv2.rectangle(
            canvas,
            (label_left, label_bottom - label_height - baseline - 3),
            (label_left + label_width + 4, label_bottom + 2),
            color,
            cv2.FILLED,
        )
        cv2.putText(
            canvas,
            label,
            (label_left + 2, label_bottom),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.32,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
    ok, encoded = cv2.imencode(".jpg", canvas)
    if not ok:
        raise RuntimeError("Could not encode annotated image")
    return encoded.tobytes()
