from __future__ import annotations

import concurrent.futures
from dataclasses import asdict
import numpy as np

from app.adapters.attribute_extractor_protocol import AttributeExtractor
from app.adapters.plate_localizer_protocol import PlateLocalizer
from app.adapters.plate_reader_protocol import PlateReader
from app.services.plate_consensus import PlateCandidate, consensus
from app.services.plate_quality import conservative_enhance


class EnrichmentProcessor:
    def __init__(self, attributes: AttributeExtractor | None, localizer: PlateLocalizer | None,
                 reader: PlateReader | None, retry_threshold: float, accept_threshold: float) -> None:
        self.attributes, self.localizer, self.reader = attributes, localizer, reader
        self.retry_threshold, self.accept_threshold = retry_threshold, accept_threshold

    def enrich(self, crop: np.ndarray, frame_index: int | None = None) -> tuple[dict, dict]:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            attributes_future = executor.submit(self._attributes, crop, frame_index)
            plate_future = executor.submit(self._plate, crop, frame_index)
            return attributes_future.result(), plate_future.result()

    def _attributes(self, crop: np.ndarray, frame_index: int | None) -> dict:
        if self.attributes is None: return {"status": "failed", "items": [], "error_code": "attribute_model_unavailable"}
        try:
            return {"status": "completed", "items": [{**asdict(item), "evidence_frame_index": frame_index} for item in self.attributes.extract(crop)]}
        except Exception: return {"status": "failed", "items": [], "error_code": "attribute_processing_failed"}

    def _plate(self, crop: np.ndarray, frame_index: int | None) -> dict:
        if self.localizer is None or self.reader is None: return {"status": "failed", "used_enhancement": False, "evidence_frame_indexes": [], "error_code": "plate_model_unavailable"}
        try:
            location = self.localizer.locate(crop)
            if location is None: return {"status": "not_detected", "used_enhancement": False, "evidence_frame_indexes": []}
            height, width = crop.shape[:2]
            x1, y1, x2, y2 = max(0, location.x_min), max(0, location.y_min), min(width, location.x_max), min(height, location.y_max)
            if x2 <= x1 or y2 <= y1: return {"status": "unreadable", "used_enhancement": False, "evidence_frame_indexes": []}
            plate = crop[y1:y2, x1:x2]; reading = self.reader.read(plate); enhanced = False
            if reading is None or reading.confidence < self.retry_threshold:
                enhanced, retried = True, self.reader.read(conservative_enhance(plate))
                if retried is not None and (reading is None or retried.confidence > reading.confidence): reading = retried
            output = {"status": "unreadable", "bbox_relative": {"x_min": x1 / width, "y_min": y1 / height, "x_max": x2 / width, "y_max": y2 / height}, "localizer_confidence": location.confidence, "ocr_confidence": reading.confidence if reading else None, "used_enhancement": enhanced, "evidence_frame_indexes": [] if frame_index is None else [frame_index]}
            if reading is not None and reading.confidence >= self.accept_threshold:
                output.update({"status": "read", "text": reading.text})
            return output
        except Exception:
            return {"status": "failed", "used_enhancement": False, "evidence_frame_indexes": [], "error_code": "plate_processing_failed"}
