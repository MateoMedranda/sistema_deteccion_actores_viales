from __future__ import annotations

from contextlib import nullcontext
import numpy as np
from app.domain.models import Detection


class YOLOv10ByteTrackAdapter:
    """One source-frame clock and ByteTrack state per job, shared detector weights.

    Interval 1 preserves the existing predict/update path. Interval 2 predicts the
    Kalman state on intermediate source frames WITHOUT an empty detector update:
    an intentionally unobserved frame must not mark active vehicles as lost.
    """

    def __init__(self, model, confidence_threshold: float, device: str) -> None:
        self._model = model
        self._confidence_threshold = confidence_threshold
        self._device = device
        self.detection_interval = 1
        self.reset()

    def reset(self) -> None:
        self._tracker = None
        self._source_index = 0
        self.last_was_detection = True

    def set_detection_interval(self, interval: int) -> None:
        if type(interval) is not int or interval not in (1, 2):
            raise ValueError("invalid_detection_interval")
        if self._source_index:
            raise ValueError("detection_interval_already_started")
        self.detection_interval = interval

    @property
    def requires_detection(self) -> bool:
        return self._source_index % self.detection_interval == 0

    def track(self, frame: np.ndarray) -> list[tuple[Detection, int]]:
        return self._track(frame)

    def track_profiled(self, frame, profile):
        return self._track(frame, profile)

    def _predict_intermediate(self):
        from ultralytics.trackers.basetrack import TrackState

        tracker = self._tracker
        # update() advances the clock and predicts once on observed frames.
        # Here do those two operations once for the unobserved source frame.
        tracker.frame_id += 1
        active = [t for t in tracker.tracked_stracks
                  if t.is_activated and t.state == TrackState.Tracked]
        pool = {t.track_id: t for t in (*active, *tracker.lost_stracks)}
        tracker.multi_predict(list(pool.values()))
        # Do not fabricate a measurement, activation, score, ID or last-seen time.
        # Lost/unconfirmed tracks remain hidden until an actual association.
        return [t.result for t in active]

    def _track(self, frame, profile=None):
        measure = profile.measure if profile is not None else lambda stage: nullcontext()
        if self._tracker is None:
            with measure("tracking"):
                from ultralytics.trackers.byte_tracker import BYTETracker
                from ultralytics.utils import YAML, IterableSimpleNamespace
                from ultralytics.utils.checks import check_yaml
                self._tracker = BYTETracker(args=IterableSimpleNamespace(**YAML.load(check_yaml("bytetrack.yaml"))))
        self.last_was_detection = self.requires_detection
        if self.last_was_detection:
            with measure("detection"):
                result = self._model.predict(frame, conf=self._confidence_threshold,
                    device=self._device, verbose=False, mode="predict")[0]
                detections = result.boxes.cpu().numpy()
            with measure("tracking"):
                tracks = self._tracker.update(detections, result.orig_img)
                output = self._convert(tracks, frame.shape[:2])
        else:
            with measure("tracking"):
                output = self._convert(self._predict_intermediate(), frame.shape[:2])
        self._source_index += 1
        return output

    def _convert(self, tracks, shape):
        output = []
        height, width = shape
        for row in tracks:
            # Kalman predictions may extend outside the source. Keep the existing
            # clipping, never clamp the tracker's internal state itself.
            x1, y1, x2, y2 = map(int, row[:4])
            x1, x2 = max(0, min(width, x1)), max(0, min(width, x2))
            y1, y2 = max(0, min(height, y1)), max(0, min(height, y2))
            if x2 <= x1 or y2 <= y1:
                continue
            tid, score, cls = int(row[4]), float(row[5]), int(row[6])
            output.append((Detection(cls, str(self._model.names[cls]), score, x1, y1, x2, y2), tid))
        return output
