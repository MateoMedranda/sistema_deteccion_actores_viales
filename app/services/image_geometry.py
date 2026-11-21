"""One half-open pixel geometry shared by detection, annotation and evidence."""
from dataclasses import replace
import math

def clip_box(x_min, y_min, x_max, y_max, width: int, height: int):
    values = (x_min, y_min, x_max, y_max)
    if width <= 0 or height <= 0 or not all(math.isfinite(float(v)) for v in values):
        return None
    x1, y1 = max(0, min(width, int(x_min))), max(0, min(height, int(y_min)))
    x2, y2 = max(0, min(width, int(x_max))), max(0, min(height, int(y_max)))
    return (x1, y1, x2, y2) if x2 > x1 and y2 > y1 else None

def canonical_detections(detections, width: int, height: int):
    result = []
    for detection in detections:
        box = clip_box(detection.x_min, detection.y_min, detection.x_max, detection.y_max, width, height)
        if box is not None:
            result.append(replace(detection, x_min=box[0], y_min=box[1], x_max=box[2], y_max=box[3]))
    return result
