from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path


class AnalysisStatus(StrEnum):
    RECEIVED = "received"
    VALIDATED = "validated"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"


class VideoJobStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


VIDEO_TERMINAL_STATES = {VideoJobStatus.COMPLETED, VideoJobStatus.FAILED, VideoJobStatus.CANCELLED}
VIDEO_TRANSITIONS = {
    VideoJobStatus.QUEUED: {VideoJobStatus.PROCESSING, VideoJobStatus.CANCELLED, VideoJobStatus.FAILED},
    VideoJobStatus.PROCESSING: {VideoJobStatus.COMPLETED, VideoJobStatus.CANCELLED, VideoJobStatus.FAILED},
    VideoJobStatus.COMPLETED: set(),
    VideoJobStatus.FAILED: set(),
    VideoJobStatus.CANCELLED: set(),
}


def may_transition(current: VideoJobStatus, target: VideoJobStatus) -> bool:
    return target in VIDEO_TRANSITIONS[current]


@dataclass(frozen=True)
class VideoMetadata:
    media_type: str
    container: str
    codec: str
    size_bytes: int
    duration_seconds: float
    width: int
    height: int
    fps: float
    total_frames: int


@dataclass(frozen=True)
class VideoJob:
    job_id: str
    owner_key_id: str
    status: VideoJobStatus
    metadata: VideoMetadata
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    staged_path: Path | None = None
    output_path: Path | None = None
    processed_frames: int = 0
    error_code: str | None = None


@dataclass(frozen=True)
class FrameDetection:
    frame_index: int
    track_id: int
    class_id: int
    class_name: str
    confidence: float
    x_min: int
    y_min: int
    x_max: int
    y_max: int


@dataclass(frozen=True)
class VideoResult:
    job_id: str
    class_summary: dict[str, int]
    detections: list[FrameDetection]


@dataclass(frozen=True)
class VideoArtifact:
    job_id: str
    path: Path
    expires_at: datetime


@dataclass(frozen=True)
class AnalysisRequest:
    request_id: str
    source_type: str
    status: AnalysisStatus
    submitted_at: datetime
    processing_time_ms: int | None = None
    error_code: str | None = None
    validation_ms: int | None = None
    inference_ms: int | None = None
    annotation_ms: int | None = None

    @classmethod
    def received(cls, request_id: str, source_type: str = "image") -> "AnalysisRequest":
        return cls(
            request_id=request_id,
            source_type=source_type,
            status=AnalysisStatus.RECEIVED,
            submitted_at=datetime.now(UTC),
        )

    def transition(
        self,
        status: AnalysisStatus,
        *,
        processing_time_ms: int | None = None,
        error_code: str | None = None,
        validation_ms: int | None = None,
        inference_ms: int | None = None,
        annotation_ms: int | None = None,
    ) -> "AnalysisRequest":
        return replace(
            self,
            status=status,
            processing_time_ms=processing_time_ms if processing_time_ms is not None else self.processing_time_ms,
            error_code=error_code,
            validation_ms=validation_ms if validation_ms is not None else self.validation_ms,
            inference_ms=inference_ms if inference_ms is not None else self.inference_ms,
            annotation_ms=annotation_ms if annotation_ms is not None else self.annotation_ms,
        )


@dataclass(frozen=True)
class Detection:
    class_id: int
    class_name: str
    confidence: float
    x_min: int
    y_min: int
    x_max: int
    y_max: int


@dataclass(frozen=True)
class ValidatedImage:
    data: bytes
    media_type: str
    width: int
    height: int
    original_filename: str | None


@dataclass(frozen=True)
class TemporaryArtifact:
    request_id: str
    path: Path
    expires_at: datetime
