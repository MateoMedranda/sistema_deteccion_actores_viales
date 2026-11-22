from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from time import perf_counter

import psutil

from app.api.error_handlers import ApiError
from app.domain.models import CountEvent, CountJob, CountJobStatus, VideoJobStatus
from app.services.count_annotation_service import CountAnnotationService
from app.services.count_job_store import CountJobStore
from app.services.line_counting import detection_center, direction, side_of_line
from app.services.video_artifacts import VideoArtifactStore
from app.services.video_job_store import VideoJobStore


class CountProcessingError(RuntimeError):
    """Expected safe failures while calculating a line count."""


class CountProcessor:
    def __init__(
        self,
        count_store: CountJobStore,
        video_store: VideoJobStore,
        artifacts: VideoArtifactStore,
        annotation_service: CountAnnotationService,
        logger,
    ) -> None:
        self.count_store = count_store
        self.video_store = video_store
        self.artifacts = artifacts
        self.annotation_service = annotation_service
        self.logger = logger

    def process(self, job: CountJob) -> None:
        started = perf_counter()
        output: Path | None = None
        try:
            source = self.video_store.get(job.source_video_job_id, job.owner_key_id)
            if source.status is not VideoJobStatus.COMPLETED or source.output_path is None or not source.output_path.is_file():
                raise CountProcessingError("source_not_ready")
            detections = self.video_store.all_detections(job.source_video_job_id, job.owner_key_id)
            by_frame: dict[int, list] = defaultdict(list)
            for detection in detections:
                by_frame[detection.frame_index].append(detection)
            last_nonzero_side: dict[int, int] = {}
            counted_tracks: set[int] = set()
            for frame_index in range(job.total_frames):
                self._ensure_source_is_active(job)
                for detection in by_frame.get(frame_index, []):
                    track_id = detection.track_id
                    current_side = side_of_line(
                        detection_center(detection, source.metadata.width, source.metadata.height), job.line
                    )
                    previous_side = last_nonzero_side.get(track_id)
                    if current_side == 0:
                        continue
                    if previous_side is not None and track_id not in counted_tracks:
                        crossing_direction = direction(previous_side, current_side)
                        if crossing_direction is not None:
                            event = CountEvent(
                                job.count_job_id, track_id, detection.class_id, detection.class_name,
                                crossing_direction, frame_index, frame_index / max(source.metadata.fps, 1.0),
                            )
                            if self.count_store.record_event(event):
                                counted_tracks.add(track_id)
                    last_nonzero_side[track_id] = current_side
                self.count_store.progress(job.count_job_id, frame_index + 1)
            self._ensure_source_is_active(job)
            events = self.count_store.all_events(job.count_job_id, job.owner_key_id)
            output = self.artifacts.count_output_path()
            self.annotation_service.render(job, source.output_path, output, detections, events)
            self._ensure_source_is_active(job)
            if not self.count_store.finish(job.count_job_id, output):
                self._ensure_count_is_active(job)
                raise CountProcessingError("count_not_active")
            self.logger.info("count_job_completed", extra={
                "count_job_id": job.count_job_id,
                "source_video_job_id": job.source_video_job_id,
                "duration_ms": round((perf_counter() - started) * 1000),
                "events": len(events),
                "memory_mb": round(psutil.Process().memory_info().rss / 1024 / 1024, 2),
            })
        except Exception:
            if output is not None:
                self.artifacts.remove(output)
            raise

    def _ensure_source_is_active(self, job: CountJob) -> None:
        self._ensure_count_is_active(job)
        try:
            source = self.video_store.get(job.source_video_job_id, job.owner_key_id)
        except ApiError as exc:
            if exc.status_code in {404, 410}:
                raise CountProcessingError("source_expired") from exc
            raise
        if source.status is not VideoJobStatus.COMPLETED:
            raise CountProcessingError("source_not_ready")

    def _ensure_count_is_active(self, job: CountJob) -> None:
        if self.count_store.is_cancelled(job.count_job_id):
            raise CountProcessingError("count_cancelled")
        if not self.count_store.is_active(job.count_job_id):
            raise CountProcessingError("count_expired")
