from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

from app.domain.models import Detection


class YOLOv10Detector:
    def __init__(self, weights_path: Path, confidence_threshold: float, device: str, ultralytics_path: Path | None = None) -> None:
        if ultralytics_path and str(ultralytics_path) not in sys.path:
            sys.path.insert(0, str(ultralytics_path))
        from ultralytics import YOLO

        self._model = YOLO(str(weights_path))
        self._confidence_threshold = confidence_threshold
        self._device = device
        self._model_name = weights_path.name

    @property
    def model_name(self) -> str:
        return self._model_name

    def detect(self, image: np.ndarray) -> list[Detection]:
        result = self._model(image, conf=self._confidence_threshold, device=self._device, verbose=False)[0]
        detections: list[Detection] = []
        for box in result.boxes:
            x_min, y_min, x_max, y_max = map(int, box.xyxy[0].tolist())
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            detections.append(
                Detection(
                    class_id=class_id,
                    class_name=str(self._model.names[class_id]),
                    confidence=confidence,
                    x_min=max(0, x_min),
                    y_min=max(0, y_min),
                    x_max=max(1, x_max),
                    y_max=max(1, y_max),
                )
            )
        return detections
