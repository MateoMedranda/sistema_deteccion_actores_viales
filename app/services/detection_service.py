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
from app.domain.schemas import AnnotatedImage, BoundingBox, DetectionResponse, DetectionResponseItem, ImageMetadata
from app.services.annotation_service import annotate
from app.services.temporary_artifacts import TemporaryArtifactStore


class DetectionService:
    def __init__(
        self,
        detector: Detector | None,
        artifacts: TemporaryArtifactStore,
        logger: logging.Logger,
        max_concurrent_inferences: int = 1,
    ) -> None:
        self.detector = detector
        self.artifacts = artifacts
        self.logger = logger
        self._inference_slots = threading.BoundedSemaphore(max_concurrent_inferences)
        self._requests: dict[str, AnalysisRequest] = {}
        self._requests_lock = threading.Lock()

    def begin(self, request_id: str, source_type: str = "image") -> AnalysisRequest:
        request = AnalysisRequest.received(request_id, source_type)
        with self._requests_lock:
            self._requests[request_id] = request
        return request

    def reject(self, request_id: str, error_code: str, validation_ms: int) -> AnalysisRequest:
        request = self._get_or_begin(request_id).transition(
            AnalysisStatus.REJECTED,
            processing_time_ms=validation_ms,
            validation_ms=validation_ms,
            error_code=error_code,
        )
        self._store_request(request)
        self.logger.info(
            "analysis_rejected",
            extra={
                "request_id": request_id,
                "source_type": request.source_type,
                "status": request.status,
                "validation_ms": validation_ms,
                "total_ms": validation_ms,
                "error_code": error_code,
            },
        )
        return request

    def request_state(self, request_id: str) -> AnalysisRequest | None:
        with self._requests_lock:
            return self._requests.get(request_id)

    def analyze(
        self, request_id: str, image: ValidatedImage, validation_ms: int = 0
    ) -> DetectionResponse:
        request = self._get_or_begin(request_id).transition(
            AnalysisStatus.VALIDATED, validation_ms=validation_ms
        )
        self._store_request(request)
        if self.detector is None:
            self._fail(request, "model_unavailable", validation_ms)
            raise ApiError(503, "model_unavailable", "The detection model is not ready.")
        started = perf_counter()
        decoded = cv2.imdecode(np.frombuffer(image.data, dtype=np.uint8), cv2.IMREAD_COLOR)
        if decoded is None:
            self._fail(request, "undecodable_image", validation_ms)
            raise ApiError(422, "undecodable_image", "The image cannot be decoded safely.")
        request = request.transition(AnalysisStatus.PROCESSING)
        self._store_request(request)
        before_inference = perf_counter()
        try:
            with self._inference_slots:
                detections = self.detector.detect(decoded)
        except Exception as exc:
            self._fail(request, "model_unavailable", validation_ms, exc)
            raise ApiError(503, "model_unavailable", "The image could not be analyzed at this time.") from exc
        before_annotation = perf_counter()
        annotated_bytes = annotate(decoded, detections)
        artifact = self.artifacts.save(request_id, annotated_bytes)
        finished = perf_counter()
        inference_ms = round((before_annotation - before_inference) * 1000)
        annotation_ms = round((finished - before_annotation) * 1000)
        total_ms = round((finished - started) * 1000)
        request = request.transition(
            AnalysisStatus.COMPLETED,
            processing_time_ms=total_ms,
            validation_ms=validation_ms,
            inference_ms=inference_ms,
            annotation_ms=annotation_ms,
        )
        self._store_request(request)
        self.logger.info(
            "analysis_completed",
            extra={
                "request_id": request_id,
                "status": "completed",
                "source_type": request.source_type,
                "validation_ms": validation_ms,
                "inference_ms": inference_ms,
                "annotation_ms": annotation_ms,
                "total_ms": total_ms,
            },
        )
        return DetectionResponse(
            request_id=request_id,
            processing_time_ms=total_ms,
            image=ImageMetadata(width=image.width, height=image.height, media_type=image.media_type),
            detections=[
                self._to_response(index + 1, detection, image.width, image.height)
                for index, detection in enumerate(detections)
            ],
            annotated_image=AnnotatedImage(
                url=f"/api/v1/detections/{request_id}/annotated-image",
                expires_at=artifact.expires_at,
            ),
        )

    def _get_or_begin(self, request_id: str) -> AnalysisRequest:
        with self._requests_lock:
            request = self._requests.get(request_id)
        return request if request is not None else self.begin(request_id)

    def _store_request(self, request: AnalysisRequest) -> None:
        with self._requests_lock:
            self._requests[request.request_id] = request

    def _fail(
        self,
        request: AnalysisRequest,
        error_code: str,
        validation_ms: int,
        exception: Exception | None = None,
    ) -> None:
        total_ms = round((datetime.now(UTC) - request.submitted_at).total_seconds() * 1000)
        failed = request.transition(
            AnalysisStatus.FAILED,
            processing_time_ms=max(0, total_ms),
            validation_ms=validation_ms,
            error_code=error_code,
        )
        self._store_request(failed)
        log = self.logger.exception if exception else self.logger.info
        log(
            "analysis_failed",
            extra={
                "request_id": request.request_id,
                "source_type": request.source_type,
                "status": failed.status,
                "validation_ms": validation_ms,
                "total_ms": failed.processing_time_ms,
                "error_code": error_code,
            },
        )

    @staticmethod
    def _to_response(
        detection_id: int, detection: Detection, image_width: int, image_height: int
    ) -> DetectionResponseItem:
        x_min = min(max(0, detection.x_min), image_width - 1)
        y_min = min(max(0, detection.y_min), image_height - 1)
        x_max = min(max(x_min + 1, detection.x_max), image_width)
        y_max = min(max(y_min + 1, detection.y_max), image_height)
        return DetectionResponseItem(
            detection_id=detection_id,
            class_id=detection.class_id,
            class_name=detection.class_name,
            confidence=detection.confidence,
            bbox=BoundingBox(
                x_min=x_min,
                y_min=y_min,
                x_max=x_max,
                y_max=y_max,
            ),
        )
