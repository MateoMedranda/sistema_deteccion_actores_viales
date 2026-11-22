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


class CountJobStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EnrichmentJobStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


ENRICHMENT_TERMINAL_STATES = {
    EnrichmentJobStatus.COMPLETED, EnrichmentJobStatus.FAILED, EnrichmentJobStatus.CANCELLED,
}
ENRICHMENT_TRANSITIONS = {
    EnrichmentJobStatus.QUEUED: {EnrichmentJobStatus.PROCESSING, EnrichmentJobStatus.FAILED, EnrichmentJobStatus.CANCELLED},
    EnrichmentJobStatus.PROCESSING: {EnrichmentJobStatus.COMPLETED, EnrichmentJobStatus.FAILED, EnrichmentJobStatus.CANCELLED},
    EnrichmentJobStatus.COMPLETED: set(), EnrichmentJobStatus.FAILED: set(), EnrichmentJobStatus.CANCELLED: set(),
}


def may_transition_enrichment(current: EnrichmentJobStatus, target: EnrichmentJobStatus) -> bool:
    return target in ENRICHMENT_TRANSITIONS[current]


COUNT_TERMINAL_STATES = {CountJobStatus.COMPLETED, CountJobStatus.FAILED, CountJobStatus.CANCELLED}
COUNT_TRANSITIONS = {
    CountJobStatus.QUEUED: {CountJobStatus.PROCESSING, CountJobStatus.CANCELLED, CountJobStatus.FAILED},
    CountJobStatus.PROCESSING: {CountJobStatus.COMPLETED, CountJobStatus.CANCELLED, CountJobStatus.FAILED},
    CountJobStatus.COMPLETED: set(),
    CountJobStatus.FAILED: set(),
    CountJobStatus.CANCELLED: set(),
}


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


def may_transition_count(current: CountJobStatus, target: CountJobStatus) -> bool:
    return target in COUNT_TRANSITIONS[current]


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

    processing_phase: str | None = None
    frame_total_confirmed: bool = False
    video_metadata: dict | None = None
    eligible_track_count: int | None = None
    classes_present: list[str] | None = None


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
class CountPoint:
    x: float
    y: float


@dataclass(frozen=True)
class CountLine:
    point_a: CountPoint
    point_b: CountPoint


@dataclass(frozen=True)
class CountJob:
    count_job_id: str
    source_video_job_id: str
    owner_key_id: str
    status: CountJobStatus
    line: CountLine
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    total_frames: int
    processed_frames: int = 0
    output_path: Path | None = None
    error_code: str | None = None


@dataclass(frozen=True)
class CountEvent:
    count_job_id: str
    track_id: int
    class_id: int
    class_name: str
    direction: str
    frame_index: int
    video_time_seconds: float


@dataclass(frozen=True)
class CountSummary:
    class_name: str
    direction: str
    total: int


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
    owner_key_id: str | None = None


@dataclass(frozen=True)
class EnrichmentJob:
    enrichment_job_id: str
    source_kind: str
    source_id: str
    owner_key_id: str
    status: EnrichmentJobStatus
    total_units: int
    processed_units: int
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    error_code: str | None = None


@dataclass(frozen=True)
class EnrichmentUnit:
    unit_id: str
    enrichment_job_id: str
    detection_id: int
    track_id: int | None
    class_id: int
    class_name: str
    evidence_frame_indexes: tuple[int, ...]


@dataclass(frozen=True)
class AttributeResult:
    unit_id: str
    attribute_name: str
    label: str
    confidence: float
    evidence_frame_index: int | None


@dataclass(frozen=True)
class PlateResult:
    unit_id: str
    status: str
    plate_text: str | None
    localizer_confidence: float | None
    ocr_confidence: float | None


@dataclass(frozen=True)
class PlateCandidate:
    unit_id: str
    text: str | None
    confidence: float | None
    frame_index: int | None
