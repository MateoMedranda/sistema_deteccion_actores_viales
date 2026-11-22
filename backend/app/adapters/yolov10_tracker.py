from __future__ import annotations

import numpy as np

from app.domain.models import Detection


class YOLOv10ByteTrackAdapter:
    """Per-job Ultralytics ByteTrack session; the YOLO model object is shared, tracker state is not."""

    def __init__(self, model, confidence_threshold: float, device: str) -> None:
        self._model, self._confidence_threshold, self._device = model, confidence_threshold, device

    def reset(self) -> None:
        # `persist=False` on the first frame starts an independent ByteTrack session.
        self._first_frame = True

    def track(self, frame: np.ndarray) -> list[tuple[Detection, int]]:
        result = self._model.track(
            frame, conf=self._confidence_threshold, device=self._device, verbose=False,
            tracker="bytetrack.yaml", persist=not self._first_frame,
        )[0]
        self._first_frame = False
        tracked: list[tuple[Detection, int]] = []
        for box in result.boxes:
            if box.id is None:
                continue
            class_id = int(box.cls[0])
            x_min, y_min, x_max, y_max = map(int, box.xyxy[0].tolist())
            tracked.append((Detection(class_id, str(self._model.names[class_id]), float(box.conf[0]), max(0, x_min), max(0, y_min), max(1, x_max), max(1, y_max)), int(box.id[0])))
        return tracked
