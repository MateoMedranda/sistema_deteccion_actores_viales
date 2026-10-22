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
