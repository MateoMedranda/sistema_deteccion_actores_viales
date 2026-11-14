from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from app.domain.models import Detection, FrameDetection


@dataclass(frozen=True)
class VehicleCrop:
    image: np.ndarray
    x_min: int
    y_min: int
    x_max: int
    y_max: int


def crop_vehicle(image: np.ndarray, detection: Detection | FrameDetection, vehicle_classes: set[str]) -> VehicleCrop | None:
    if detection.class_name.lower() not in vehicle_classes:
        return None
    height, width = image.shape[:2]
    x_min = max(0, min(width, int(detection.x_min))); y_min = max(0, min(height, int(detection.y_min)))
    x_max = max(0, min(width, int(detection.x_max))); y_max = max(0, min(height, int(detection.y_max)))
    if x_max <= x_min or y_max <= y_min:
        return None
    return VehicleCrop(image[y_min:y_max, x_min:x_max].copy(), x_min, y_min, x_max, y_max)
