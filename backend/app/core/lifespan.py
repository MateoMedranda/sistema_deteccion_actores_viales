from __future__ import annotations

from contextlib import asynccontextmanager
import subprocess
import threading

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
from app.services.video_progressive_store import ProgressiveStore
from app.services.video_progressive_service import ProgressiveService
from app.services.progressive_evidence import ProgressiveEvidence
from app.services.progressive_enrichment import ProgressiveEnrichment
from app.services.video_worker import VideoWorker
from app.services.video_job_service import VideoJobService
from app.services.count_annotation_service import CountAnnotationService
from app.services.count_job_service import CountJobService
from app.services.count_job_store import CountJobStore
from app.services.count_processing import CountProcessor
from app.services.count_worker import CountWorker
from app.services.source_artifacts import SourceArtifactStore
from app.services.image_detection_store import ImageDetectionStore
from app.services.enrichment_job_store import EnrichmentJobStore
from app.services.enrichment_job_service import EnrichmentJobService
from app.services.enrichment_processing import EnrichmentProcessor
from app.services.enrichment_worker import EnrichmentWorker
from app.services.temporary_cleanup import PeriodicCleanup
from app.services.plate_preview_store import PlatePreviewStore
from app.services.plate_preview_service import PlatePreviewService
from app.adapters.efficientnet_attribute_extractor import EfficientNetAttributeExtractor
from app.adapters.yolov8_plate_localizer import YOLOv8PlateLocalizer
from app.adapters.paddle_plate_reader import PaddlePlateReader


def build_lifespan(settings: Settings, injected_detector: Detector | None = None):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger = configure_logging()
        artifacts = TemporaryArtifactStore(settings.temp_artifact_dir, settings.artifact_ttl_seconds)
        video_artifacts = VideoArtifactStore(settings.video_temp_dir)
        count_artifacts = VideoArtifactStore(settings.count_temp_dir)
        video_jobs = VideoJobStore(settings.video_job_db_path, settings.video_result_ttl_seconds, settings.max_queued_video_jobs)
        progressive=ProgressiveStore(settings.video_job_db_path,video_jobs,settings.video_progressive_buffer_seconds)
        evidence=ProgressiveEvidence(progressive,settings.video_temp_dir/"progressive-evidence",settings.vehicle_class_set(),settings.max_evidence_frames_per_track)
        evidence.initialize()
        app.state.progressive_store=progressive
        app.state.progressive=ProgressiveService(progressive,video_jobs)
        app.state.progressive_evidence=evidence
        from app.services.progressive_counting import ProgressiveCountService
        app.state.progressive_count=ProgressiveCountService(progressive)
        def source_guard(job,owner):
            if progressive.exists(job):
                with progressive.lock:progressive.row(job,owner)
        video_artifacts.retained=progressive.retained
        count_jobs = CountJobStore(settings.count_job_db_path, settings.count_result_ttl_seconds, settings.max_queued_count_jobs)
        enrichment_artifacts = SourceArtifactStore(settings.enrichment_temp_dir)
        image_sources = ImageDetectionStore(enrichment_artifacts, settings.artifact_ttl_seconds)
        enrichment_jobs = EnrichmentJobStore(settings.enrichment_job_db_path, settings.enrichment_result_ttl_seconds, settings.max_queued_enrichment_jobs)
        count_jobs.source_guard=source_guard
        enrichment_jobs.source_guard=source_guard
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
                logger.error("model_initialization_failed", extra={"error_code":"model_initialization_failed"})
        app.state.settings = settings
        app.state.service = DetectionService(
            detector, artifacts, logger, settings.max_concurrent_inferences, image_sources, settings.vehicle_class_set
        )
        app.state.ready = detector is not None
        app.state.video_probe = FFprobeAdapter(settings.ffprobe_executable)
        app.state.video_artifacts = video_artifacts
        app.state.video_jobs = video_jobs
        app.state.video_job_service = VideoJobService(settings, app.state.video_probe, video_jobs, video_artifacts)
        app.state.video_job_service.progressive=progressive
        app.state.count_jobs = count_jobs
        app.state.count_job_service = CountJobService(settings, count_jobs, video_jobs, count_artifacts, logger)
        app.state.video_tools_ready = _video_tools_available(settings)
        app.state.image_sources = image_sources
        app.state.enrichment_jobs = enrichment_jobs
        app.state.enrichment_job_service = EnrichmentJobService(settings, enrichment_jobs, image_sources, video_jobs)
        attributes = localizer = reader = None
        try:
            if settings.attribute_model_weights_path and settings.attribute_model_manifest_path:
                attributes = EfficientNetAttributeExtractor(settings.attribute_model_weights_path, settings.attribute_model_manifest_path, settings.inference_device)
        except Exception:
            logger.error("attribute_model_initialization_failed", extra={"error_code":"attribute_model_initialization_failed"})
        try:
            if settings.plate_model_weights_path:
                localizer = YOLOv8PlateLocalizer(settings.plate_model_weights_path, settings.plate_localizer_threshold)
                reader = PaddlePlateReader(settings.paddle_ocr_lang)
        except Exception:
            logger.error("plate_model_initialization_failed", extra={"error_code":"plate_model_initialization_failed"})
        enrichment_processor = EnrichmentProcessor(attributes, localizer, reader, settings.plate_ocr_retry_threshold, settings.plate_ocr_accept_threshold, settings.max_concurrent_attribute_inferences, settings.max_concurrent_plate_inferences)
        enrichment_processor.logger = logger
        app.state.enrichment_job_service.processor = enrichment_processor
        app.state.enrichment_job_service.progressive=evidence
        app.state.enrichment_models_ready = all(value == "ready" for value in enrichment_processor.capabilities.values())
        enrichment_worker = EnrichmentWorker(enrichment_jobs, app.state.enrichment_job_service, enrichment_processor, logger)
        enrichment_worker.start(); app.state.enrichment_worker = enrichment_worker
        progressive_slots=threading.Lock()
        progressive_worker=ProgressiveEnrichment(evidence,enrichment_processor,logger,progressive_slots)
        progressive_worker.start()
        app.state.progressive_worker=progressive_worker
        video_worker = None
        if detector is not None:
            video_worker = VideoWorker(
                VideoProcessor(
                    detector, video_jobs, video_artifacts, settings.ffmpeg_executable,
                    settings.video_job_timeout_seconds, logger, settings.vehicle_class_set(),
                ),
                video_jobs,
                logger,
            )
            video_worker.processor.profile_root=settings.video_job_db_path.parent / "video-profiles"
            video_worker.processor.progressive_inference_slots=progressive_slots
            video_worker.processor.progressive=progressive
            video_worker.processor.evidence=evidence
            video_worker.processor.progressive_batch_frames=settings.video_progressive_batch_frames
            video_worker.processor.progressive_batch_us=round(settings.video_progressive_batch_seconds*1e6)
            video_worker.start()
        app.state.video_worker = video_worker
        count_workers = [
            CountWorker(
                CountProcessor(count_jobs, video_jobs, count_artifacts, CountAnnotationService(), logger),
                count_jobs, count_artifacts, logger,
            )
            for _ in range(settings.max_concurrent_count_jobs)
        ]
        for count_worker in count_workers:
            count_worker.start()
        app.state.count_worker = count_workers[0]
        app.state.count_workers = count_workers
        preview_store=PlatePreviewStore()
        app.state.plate_preview_store=preview_store
        app.state.plate_preview_service=PlatePreviewService(enrichment_jobs,image_sources,preview_store)
        janitor = PeriodicCleanup((progressive,evidence,image_sources, enrichment_jobs, artifacts, app.state.video_job_service, count_jobs, preview_store), logger)
        app.state.temporary_cleanup = janitor
        janitor.start()
        yield
        janitor.close()
        app.state.plate_preview_service.close()
        preview_store.close()
        for count_worker in count_workers:
            count_worker.close()
        enrichment_worker.close()
        if video_worker is not None:
            video_worker.close()
        progressive_worker.close()
        enrichment_processor.close()
        progressive.close()
        artifacts.close()
        video_artifacts.close()
        video_jobs.close()
        count_jobs.close()
        enrichment_jobs.close()
        enrichment_artifacts.close()
        count_artifacts.close()

    return lifespan


def _video_tools_available(settings: Settings) -> bool:
    try:
        for executable in (settings.ffmpeg_executable, settings.ffprobe_executable):
            subprocess.run([executable, "-version"], capture_output=True, check=True, timeout=5)
    except (FileNotFoundError, subprocess.SubprocessError, OSError):
        return False
    return True
