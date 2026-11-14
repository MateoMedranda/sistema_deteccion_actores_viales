from __future__ import annotations
import logging
import threading
import time
import cv2

from app.services.enrichment_job_service import EnrichmentJobService
from app.services.enrichment_processing import EnrichmentProcessor
from app.services.vehicle_cropping import crop_vehicle


class EnrichmentWorker:
    def __init__(self, jobs, service: EnrichmentJobService, processor: EnrichmentProcessor, logger: logging.Logger) -> None:
        self.jobs, self.service, self.processor, self.logger = jobs, service, processor, logger
        self.stop_event = threading.Event(); self.thread = threading.Thread(target=self._run, daemon=True, name="enrichment-worker")

    def start(self) -> None: self.thread.start()
    def close(self) -> None: self.stop_event.set(); self.thread.join(timeout=2)
    def _run(self) -> None:
        while not self.stop_event.is_set():
            job = self.jobs.dequeue()
            if job is None: self.stop_event.wait(.1); continue
            try: self._process(job)
            except Exception: self.logger.exception("enrichment_job_failed", extra={"job_id": job.enrichment_job_id, "error_code": "processing_failed"}); self.jobs.fail(job.enrichment_job_id, "processing_failed")

    def _process(self, job) -> None:
        source = self.service.resolve(job.source_kind, job.source_id, job.owner_key_id)
        units = self.service.units_for_source(job.source_kind, source, job.owner_key_id); results = []
        image = cv2.imdecode(__import__("numpy").frombuffer(source.original_path.read_bytes(), dtype=__import__("numpy").uint8), cv2.IMREAD_COLOR) if job.source_kind == "image" else None
        capture = cv2.VideoCapture(str(source.staged_path)) if job.source_kind == "video" else None
        try:
            for unit in units:
                frame = image
                if capture is not None:
                    capture.set(cv2.CAP_PROP_POS_FRAMES, unit["frame_index"]); ok, frame = capture.read()
                    if not ok: continue
                crop = crop_vehicle(frame, unit["bbox"], self.service.settings.vehicle_class_set())
                if crop is None: continue
                attributes, plate = self.processor.enrich(crop.image, unit["frame_index"])
                results.append({"vehicle_key": f"track-{unit['track_id']}" if unit['track_id'] else f"detection-{unit['detection_id']}", "detection_id": unit["detection_id"], "track_id": unit["track_id"], "class_id": unit["class_id"], "class_name": unit["class_name"], "evidence_frame_indexes": [] if unit["frame_index"] is None else [unit["frame_index"]], "attributes_status": attributes["status"], "plate_status": plate["status"], "attributes": attributes["items"], "plate": plate, "error_code": attributes.get("error_code") or plate.get("error_code")})
        finally:
            if capture is not None: capture.release()
        self.jobs.finish(job.enrichment_job_id, results)
