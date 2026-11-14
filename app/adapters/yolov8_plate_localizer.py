from __future__ import annotations
from pathlib import Path
import numpy as np
from app.adapters.plate_localizer_protocol import PlateLocation


class YOLOv8PlateLocalizer:
    def __init__(self, weights_path: Path, threshold: float = .25) -> None:
        if not weights_path.is_file():
            raise RuntimeError("plate_model_not_configured")
        from ultralytics import YOLO
        self.model, self.threshold = YOLO(str(weights_path)), threshold

    def locate(self, vehicle_crop: np.ndarray) -> PlateLocation | None:
        result = self.model(vehicle_crop, verbose=False)[0]
        candidates = [box for box in result.boxes if float(box.conf[0]) >= self.threshold]
        if not candidates: return None
        best = max(candidates, key=lambda box: float(box.conf[0]))
        x1, y1, x2, y2 = (int(value) for value in best.xyxy[0].tolist())
        return PlateLocation(x1, y1, x2, y2, float(best.conf[0]))
