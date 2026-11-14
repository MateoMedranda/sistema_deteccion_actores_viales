from __future__ import annotations

import numpy as np

from app.adapters.attribute_extractor_protocol import AttributePrediction
from app.adapters.plate_localizer_protocol import PlateLocation
from app.adapters.plate_reader_protocol import PlateReading
from app.domain.models import Detection, FrameDetection


SYNTHETIC_API_KEY = "enrichment-test-key"
SYNTHETIC_IMAGE = np.full((48, 64, 3), 120, dtype=np.uint8)
VEHICLE_DETECTION = Detection(0, "car", .95, 4, 4, 40, 32)
TRACK_DETECTIONS = [FrameDetection(0, 1, 0, "car", .9, 4, 4, 40, 32), FrameDetection(1, 1, 0, "car", .95, 5, 4, 41, 32)]


class FakeAttributes:
    def extract(self, crop):
        return [AttributePrediction("color", "white", .9), AttributePrediction("type", "sedan", .8)]


class FakeLocalizer:
    def locate(self, crop): return PlateLocation(2, 2, 16, 8, .95)


class FakeReader:
    def __init__(self, reading: PlateReading | None = PlateReading("SYN123", .95)) -> None: self.reading = reading
    def read(self, crop): return self.reading
