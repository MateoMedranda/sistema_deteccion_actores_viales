from __future__ import annotations

from contextlib import asynccontextmanager
import subprocess

from fastapi import FastAPI

from app.adapters.detector_protocol import Detector
from app.adapters.yolov10_detector import YOLOv10Detector
from app.core.config import Settings
from app.core.logging import configure_logging
from app.services.detection_service import DetectionService
from app.services.temporary_artifacts import TemporaryArtifactStore
from app.adapters.video_probe import FFprobeAdapter
from app.services.video_artifacts import VideoArtifactStore
from app.services.video_job_store import VideoJobStore
from app.services.video_processing import VideoProcessor
from app.services.video_worker import VideoWorker
from app.services.video_job_service import VideoJobService


def build_lifespan(settings: Settings, injected_detector: Detector | None = None):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger = configure_logging()
        artifacts = TemporaryArtifactStore(settings.temp_artifact_dir, settings.artifact_ttl_seconds)
        video_artifacts = VideoArtifactStore(settings.video_temp_dir)
        video_jobs = VideoJobStore(settings.video_job_db_path, settings.video_result_ttl_seconds, settings.max_queued_video_jobs)
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
        app.state.video_probe = FFprobeAdapter(settings.ffprobe_executable)
        app.state.video_artifacts = video_artifacts
        app.state.video_jobs = video_jobs
        app.state.video_job_service = VideoJobService(settings, app.state.video_probe, video_jobs, video_artifacts)
        app.state.video_tools_ready = _video_tools_available(settings)
        video_worker = None
        if detector is not None:
            video_worker = VideoWorker(
                VideoProcessor(
                    detector, video_jobs, video_artifacts, settings.ffmpeg_executable,
                    settings.video_job_timeout_seconds, logger,
                ),
                video_jobs,
                logger,
            )
            video_worker.start()
        app.state.video_worker = video_worker
        yield
        if video_worker is not None:
            video_worker.close()
        artifacts.close()
        video_jobs.close()
        video_artifacts.close()

    return lifespan


def _video_tools_available(settings: Settings) -> bool:
    try:
        for executable in (settings.ffmpeg_executable, settings.ffprobe_executable):
            subprocess.run([executable, "-version"], capture_output=True, check=True, timeout=5)
    except (FileNotFoundError, subprocess.SubprocessError, OSError):
        return False
    return True
