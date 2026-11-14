from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path
from time import perf_counter

import cv2
import numpy as np
import psutil

from app.adapters.detector_protocol import Detector
from app.domain.models import Detection, FrameDetection, VideoJob
from app.services.video_artifacts import VideoArtifactStore
from app.services.video_job_store import VideoJobStore


class VideoProcessingError(RuntimeError):
    """Expected, safe failures while processing an accepted video job."""


class IoUTracker:
    """Small per-job tracker used until a separately evaluated ByteTrack adapter is introduced."""

    def __init__(self) -> None:
        self._next_id = 1
        self._previous: list[tuple[int, Detection]] = []

    def assign(self, detections: list[Detection]) -> list[int]:
        assigned: list[int] = []
        used: set[int] = set()
        for detection in detections:
            match = next(
                (
                    track_id for track_id, previous in self._previous
                    if track_id not in used and previous.class_id == detection.class_id
                    and self._iou(previous, detection) >= 0.3
                ),
                None,
            )
            if match is None:
                match = self._next_id
                self._next_id += 1
            used.add(match)
            assigned.append(match)
        self._previous = list(zip(assigned, detections, strict=True))
        return assigned

    @staticmethod
    def _iou(left: Detection, right: Detection) -> float:
        x1, y1 = max(left.x_min, right.x_min), max(left.y_min, right.y_min)
        x2, y2 = min(left.x_max, right.x_max), min(left.y_max, right.y_max)
        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        if not intersection:
            return 0.0
        left_area = (left.x_max - left.x_min) * (left.y_max - left.y_min)
        right_area = (right.x_max - right.x_min) * (right.y_max - right.y_min)
        return intersection / max(1, left_area + right_area - intersection)


class VideoProcessor:
    def __init__(
        self,
        detector: Detector,
        store: VideoJobStore,
        artifacts: VideoArtifactStore,
        ffmpeg_executable: str,
        timeout_seconds: int,
        logger,
    ) -> None:
        self.detector = detector
        self.store = store
        self.artifacts = artifacts
        self.ffmpeg_executable = ffmpeg_executable
        self.timeout_seconds = timeout_seconds
        self.logger = logger

    def process(self, job: VideoJob) -> None:
        if job.staged_path is None:
            raise VideoProcessingError("missing_input")
        capture = cv2.VideoCapture(str(job.staged_path))
        if not capture.isOpened():
            raise VideoProcessingError("invalid_video")
        temporary = self.artifacts.annotated_output_path().with_suffix(".raw.mp4")
        output = self.artifacts.annotated_output_path()
        writer = cv2.VideoWriter(
            str(temporary), cv2.VideoWriter_fourcc(*"mp4v"), job.metadata.fps,
            (job.metadata.width, job.metadata.height),
        )
        if not writer.isOpened():
            capture.release()
            raise VideoProcessingError("output_initialization_failed")
        model_tracker = self.detector.create_video_tracker() if hasattr(self.detector, "create_video_tracker") else None
        tracker = IoUTracker()
        started = perf_counter()
        detections: list[FrameDetection] = []
        frame_index = 0
        cancelled = False
        try:
            while True:
                if self.store.is_cancelled(job.job_id):
                    cancelled = True
                    break
                if perf_counter() - started > self.timeout_seconds:
                    raise VideoProcessingError("job_timeout")
                ok, frame = capture.read()
                if not ok:
                    break
                frame_started = perf_counter()
                if model_tracker is not None:
                    try:
                        pairs = model_tracker.track(frame)
                    except ModuleNotFoundError as exc:
                        # Some local Ultralytics tracker variants load SciPy lazily.  Keep the
                        # accepted job available while recording that the evaluated tracker was
                        # not available; deployments should install scipy to enable ByteTrack.
                        if exc.name != "scipy":
                            raise
                        model_tracker = None
                        self.logger.warning("video_tracker_fallback", extra={
                            "job_id": job.job_id, "error_code": "bytetrack_dependency_unavailable",
                            "tracker": "iou-fallback",
                        })
                if model_tracker is None:
                    raw = self.detector.detect(frame)
                    pairs = list(zip(raw, tracker.assign(raw), strict=True))
                for detection, track_id in pairs:
                    self._annotate(frame, detection, track_id)
                    detections.append(FrameDetection(
                        frame_index, track_id, detection.class_id, detection.class_name,
                        detection.confidence, detection.x_min, detection.y_min,
                        detection.x_max, detection.y_max,
                    ))
                writer.write(frame)
                frame_index += 1
                self.store.progress(job.job_id, frame_index)
                self.logger.info("video_frame_processed", extra={
                    "job_id": job.job_id, "progress": frame_index,
                    "frame_ms": round((perf_counter() - frame_started) * 1000),
                    "memory_mb": round(psutil.Process().memory_info().rss / 1024 / 1024, 2),
                    "tracker": "iou-fallback",
                })
        finally:
            capture.release()
            writer.release()
        if cancelled or self.store.is_cancelled(job.job_id):
            temporary.unlink(missing_ok=True)
            return
        self._encode_h264(temporary, output)
        temporary.unlink(missing_ok=True)
        self.store.finish(job.job_id, output, detections)
        # Keep the original input private until the video TTL expires: enrichment uses its
        # already computed detections and this source, never the road-actor detector again.

    def _encode_h264(self, source: Path, destination: Path) -> None:
        try:
            subprocess.run(
                [self.ffmpeg_executable, "-y", "-i", str(source), "-c:v", "libx264", "-movflags", "+faststart", str(destination)],
                check=True, capture_output=True, timeout=60,
            )
        except (FileNotFoundError, subprocess.SubprocessError, OSError) as exc:
            destination.unlink(missing_ok=True)
            raise VideoProcessingError("video_encoding_failed") from exc

    @staticmethod
    def _annotate(frame: np.ndarray, detection: Detection, track_id: int) -> None:
        cv2.rectangle(frame, (detection.x_min, detection.y_min), (detection.x_max, detection.y_max), (0, 200, 0), 2)
        cv2.putText(
            frame, f"{detection.class_name} #{track_id} {detection.confidence:.2f}",
            (detection.x_min, max(20, detection.y_min - 6)), cv2.FONT_HERSHEY_SIMPLEX,
            0.55, (0, 200, 0), 2, cv2.LINE_AA,
        )
