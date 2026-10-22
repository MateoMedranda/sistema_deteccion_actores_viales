from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.adapters.detector_protocol import Detector
from app.adapters.yolov10_detector import YOLOv10Detector
from app.core.config import Settings
from app.core.logging import configure_logging
from app.services.detection_service import DetectionService
from app.services.temporary_artifacts import TemporaryArtifactStore


def build_lifespan(settings: Settings, injected_detector: Detector | None = None):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger = configure_logging()
        artifacts = TemporaryArtifactStore(settings.temp_artifact_dir, settings.artifact_ttl_seconds)
        detector = injected_detector
        if detector is None and not settings.runtime_errors():
            try:
                detector = YOLOv10Detector(
                    settings.model_weights_path,
                    settings.model_confidence_threshold,
                    settings.inference_device,
                    settings.ultralytics_path,
                )
            except Exception:
                logger.exception("model_initialization_failed")
        app.state.settings = settings
        app.state.service = DetectionService(
            detector, artifacts, logger, settings.max_concurrent_inferences
        )
        app.state.ready = detector is not None
        yield
        artifacts.close()

    return lifespan
