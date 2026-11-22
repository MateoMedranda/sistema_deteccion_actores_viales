from dataclasses import dataclass
import numpy as np
from app.domain.models import Detection, FrameDetection
from app.services.image_geometry import clip_box

@dataclass(frozen=True)
class VehicleCrop:
    image: np.ndarray
    x_min: int
    y_min: int
    x_max: int
    y_max: int

def crop_vehicle(image: np.ndarray, detection: Detection | FrameDetection, vehicle_classes: set[str]):
    if image is None or detection.class_name.lower() not in vehicle_classes:
        return None
    height, width = image.shape[:2]
    box = clip_box(detection.x_min, detection.y_min, detection.x_max, detection.y_max, width, height)
    if box is None:
        return None
    x1, y1, x2, y2 = box
    return VehicleCrop(image[y1:y2, x1:x2].copy(), *box)
