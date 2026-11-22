from __future__ import annotations
import logging
import threading
from datetime import UTC, datetime
from time import perf_counter
import cv2
import numpy as np
from app.adapters.detector_protocol import Detector
from app.api.error_handlers import ApiError
from app.domain.models import AnalysisRequest, AnalysisStatus, Detection, ValidatedImage
from app.domain.schemas import AnnotatedImage, OriginalImage, BoundingBox, DetectionResponse, DetectionResponseItem, ImageMetadata
from app.services.annotation_service import annotate
from app.services.temporary_artifacts import TemporaryArtifactStore
from app.services.image_detection_store import ImageDetectionStore
from app.services.source_artifacts import SourceArtifactStore
from app.services.image_geometry import canonical_detections
from app.services.inference_metrics import InferenceMetrics

class DetectionService:
    def __init__(self, detector: Detector | None, artifacts: TemporaryArtifactStore, logger: logging.Logger,
                 max_concurrent_inferences=1, image_sources=None, vehicle_classes=None):
        self.detector, self.artifacts, self.logger = detector, artifacts, logger
        self._inference_slots = threading.BoundedSemaphore(max_concurrent_inferences)
        self._requests: dict[str, AnalysisRequest] = {}
        self._requests_lock = threading.Lock()
        self.image_sources = image_sources or ImageDetectionStore(
            SourceArtifactStore(artifacts.root / "sources"), int(artifacts.ttl.total_seconds()))
        self.vehicle_classes = vehicle_classes or {"car","truck","bus","van","pickup","suv","sedan","hatchback","mpv","estate"}

    def begin(self, request_id, source_type="image"):
        request = AnalysisRequest.received(request_id, source_type)
        self._store_request(request)
        return request

    def reject(self, request_id, error_code, validation_ms):
        request = self._get_or_begin(request_id).transition(AnalysisStatus.REJECTED,
            processing_time_ms=validation_ms, validation_ms=validation_ms, error_code=error_code)
        self._store_request(request)
        self.logger.info("analysis_rejected", extra={"request_id":request_id,"source_type":request.source_type,
            "status":request.status,"validation_ms":validation_ms,"total_ms":validation_ms,"error_code":error_code})
        return request

    def request_state(self, request_id):
        with self._requests_lock:
            return self._requests.get(request_id)

    def analyze(self, request_id, image: ValidatedImage, validation_ms=0, owner_key_id="default"):
        with InferenceMetrics(self.logger, "detection", request_id=request_id):
            return self._analyze(request_id, image, validation_ms, owner_key_id)

    def _analyze(self, request_id, image, validation_ms, owner_key_id):
        request = self._get_or_begin(request_id).transition(AnalysisStatus.VALIDATED, validation_ms=validation_ms)
        self._store_request(request)
        if self.detector is None:
            self._fail(request, "model_unavailable", validation_ms)
            raise ApiError(503, "model_unavailable", "The detection model is not ready.")
        started = perf_counter()
        decoded = cv2.imdecode(np.frombuffer(image.data, dtype=np.uint8), cv2.IMREAD_COLOR)
        if decoded is None:
            self._fail(request, "undecodable_image", validation_ms)
            raise ApiError(422, "undecodable_image", "The image cannot be decoded safely.")
        height, width = decoded.shape[:2]
        request = request.transition(AnalysisStatus.PROCESSING)
        self._store_request(request)
        before_inference = perf_counter()
        try:
            with self._inference_slots:
                detections = canonical_detections(self.detector.detect(decoded), width, height)
        except Exception as exc:
            self._fail(request, "model_unavailable", validation_ms)
            raise ApiError(503, "model_unavailable", "The image could not be analyzed at this time.") from exc
        before_annotation = perf_counter()
        annotated_bytes = annotate(decoded, detections)
        canonical_bytes = image.data
        if image.media_type != "image/png":
            ok, encoded = cv2.imencode(".png", decoded)
            if not ok:
                raise ApiError(503, "image_unavailable", "The image is not available.")
            canonical_bytes = encoded.tobytes()
        source = self.image_sources.create(request_id, owner_key_id, canonical_bytes, "image/png", width, height, detections)
        artifact = self.artifacts.save(request_id, annotated_bytes, owner_key_id, expires_at=source.expires_at)
        # Both stores start from the same effective deadline.
        if artifact.expires_at < source.expires_at:
            source = self.image_sources.limit_expiry(request_id,artifact.expires_at)
        finished = perf_counter()
        inference_ms = round((before_annotation - before_inference)*1000)
        annotation_ms = round((finished - before_annotation)*1000)
        total_ms = round((finished - started)*1000)
        request = request.transition(AnalysisStatus.COMPLETED, processing_time_ms=total_ms,
            validation_ms=validation_ms, inference_ms=inference_ms, annotation_ms=annotation_ms)
        self._store_request(request)
        self.logger.info("analysis_completed", extra={"request_id":request_id,"source_type":"image",
            "status":"completed","validation_ms":validation_ms,"inference_ms":inference_ms,
            "annotation_ms":annotation_ms,"total_ms":total_ms})
        eligible = self.vehicle_classes() if callable(self.vehicle_classes) else self.vehicle_classes
        return DetectionResponse(request_id=request_id, processing_time_ms=total_ms,
            image=ImageMetadata(width=width,height=height,media_type="image/png"),
            detections=[self._to_response(i+1,d,width,height,d.class_name.lower() in eligible) for i,d in enumerate(detections)],
            annotated_image=AnnotatedImage(url=f"/api/v1/detections/{request_id}/annotated-image",expires_at=source.expires_at),
            original_image=OriginalImage(url=f"/api/v1/detections/{request_id}/original-image",media_type="image/png",expires_at=source.expires_at),
            source_expires_at=source.expires_at)

    def _get_or_begin(self, request_id):
        return self.request_state(request_id) or self.begin(request_id)

    def _store_request(self, request):
        with self._requests_lock:
            self._requests[request.request_id] = request

    def _fail(self, request, error_code, validation_ms, exception=None):
        total_ms = round((datetime.now(UTC)-request.submitted_at).total_seconds()*1000)
        failed = request.transition(AnalysisStatus.FAILED,processing_time_ms=max(0,total_ms),
            validation_ms=validation_ms,error_code=error_code)
        self._store_request(failed)
        self.logger.info("analysis_failed",extra={"request_id":request.request_id,"source_type":request.source_type,
            "status":"failed","total_ms":total_ms,"error_code":error_code})

    @staticmethod
    def _to_response(detection_id, detection, image_width, image_height, enrichment_eligible=False):
        return DetectionResponseItem(detection_id=detection_id,class_id=detection.class_id,
            class_name=detection.class_name,confidence=detection.confidence,enrichment_eligible=enrichment_eligible,
            bbox=BoundingBox(x_min=detection.x_min,y_min=detection.y_min,x_max=detection.x_max,y_max=detection.y_max))
