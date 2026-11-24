"""Typed public contracts for progressive playback; generated from the approved design."""

from __future__ import annotations
from typing import Literal
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, model_validator, field_validator


class Error(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    code: str = Field(pattern="^[a-z0-9_]{1,64}$")
    message: str
    request_id: str


class BoundingBox(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    x_min: int = Field(ge=0, le=9007199254740991)
    y_min: int = Field(ge=0, le=9007199254740991)
    x_max: int = Field(ge=1, le=9007199254740991)
    y_max: int = Field(ge=1, le=9007199254740991)

    @model_validator(mode="after")
    def area(self):
        if self.x_max <= self.x_min or self.y_max <= self.y_min:
            raise ValueError("invalid_bbox")
        return self


class SourceTimeline(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    timebase: Literal["source-pts"]
    width: int = Field(ge=1, le=9007199254740991)
    height: int = Field(ge=1, le=9007199254740991)
    display_width: int = Field(ge=1, le=9007199254740991)
    display_height: int = Field(ge=1, le=9007199254740991)
    pixel_to_display: list[float] = Field(min_length=6, max_length=6)
    duration_us: int | None
    duration_confirmed: bool
    pts_origin: str = Field(pattern="^-?[0-9]{1,20}$")
    time_base_num: int = Field(ge=1, le=9007199254740991)
    time_base_den: int = Field(ge=1, le=9007199254740991)
    playback_offset_us: int = Field(ge=-9007199254740991, le=9007199254740991)


class MediaSource(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    url: str = Field(pattern="^/api/v1/video-jobs/[A-Za-z0-9_-]{1,128}/playback/source$")
    media_type: Literal["video/mp4"]
    size_bytes: int = Field(ge=1, le=9007199254740991)


class EnrichmentSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    revision: int = Field(ge=0, le=9007199254740991)
    status: Literal["discovering", "processing", "complete", "partial", "failed", "not_applicable"]
    source_closed: bool
    discovered_units: int = Field(ge=0, le=9007199254740991)
    provisional_ready_units: int = Field(ge=0, le=9007199254740991)
    terminal_units: int = Field(ge=0, le=9007199254740991)
    total_units: int | None


class PlaybackState(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    job_id: str = Field(pattern="^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
    generation: UUID
    revision: int = Field(ge=0, le=9007199254740991)
    analysis_state: Literal["queued", "analyzing", "complete", "partial_failed"]
    export_state: Literal["waiting", "queued", "encoding", "ready", "failed"]
    frames_processed: int = Field(ge=0, le=9007199254740991)
    frames_published: int = Field(ge=0, le=9007199254740991)
    available_until_us: int = Field(ge=0, le=9007199254740991)
    last_frame_start_us: int | None
    media_available: bool
    source: MediaSource | None
    timeline: SourceTimeline
    buffer_seconds: float = Field(le=30, gt=0)
    expires_at: datetime
    error_code: str | None
    enrichment: EnrichmentSummary


class Observation(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    ordinal: int = Field(ge=0, le=9007199254740991)
    track_id: int = Field(ge=1, le=9007199254740991)
    class_id: int = Field(ge=0, le=9007199254740991)
    class_name: str
    confidence: float = Field(ge=0, le=1)
    raw_bbox: BoundingBox
    display_bbox: BoundingBox | None


class FrameSlice(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    frame_index: int = Field(ge=0, le=9007199254740991)
    start_us: int = Field(ge=0, le=9007199254740991)
    end_us: int = Field(ge=1, le=9007199254740991)
    pts: str = Field(pattern="^-?[0-9]{1,20}$")
    observation_offset: int = Field(ge=0, le=9007199254740991)
    observation_total: int = Field(ge=0, le=9007199254740991)
    observations: list[Observation] = Field(max_length=1000)

    @field_validator("pts")
    @classmethod
    def signed_pts(cls, value):
        if not -(2**63) <= int(value) < 2**63:
            raise ValueError("pts_overflow")
        return value

    @model_validator(mode="after")
    def interval(self):
        if (
            self.end_us <= self.start_us
            or self.observation_offset + len(self.observations) > self.observation_total
        ):
            raise ValueError("invalid_interval")
        return self


class FramePage(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    job_id: str = Field(pattern="^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
    generation: UUID
    snapshot: int = Field(ge=0, le=9007199254740991)
    from_us: int = Field(ge=0, le=9007199254740991)
    to_us: int = Field(ge=1, le=9007199254740991)
    frames: list[FrameSlice] = Field(min_length=1, max_length=100)
    next_cursor: str | None


class Attribute(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    name: str
    value: str
    confidence: float = Field(ge=0, le=1)
    evidence_id: UUID


class Attributes(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    status: Literal["pending", "completed", "partial", "failed", "not_applicable"]
    items: list[Attribute]
    error_code: str | None


class Plate(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    status: Literal["pending", "read", "unreadable", "not_detected", "failed", "not_applicable"]
    text: str | None
    ocr_confidence: float | None
    used_enhancement: bool
    policy_id: str
    evidence_ids: list[UUID] = Field(max_length=20)
    error_code: str | None


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    evidence_id: UUID
    frame_index: int = Field(ge=0, le=9007199254740991)
    time_us: int = Field(ge=0, le=9007199254740991)
    vehicle_bbox: BoundingBox
    provisional: bool
    vehicle_url: str | None
    plate_url: str | None
    expires_at: datetime


class TrackResult(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    job_id: str = Field(pattern="^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
    generation: UUID
    unit_id: UUID
    track_id: int = Field(ge=1, le=9007199254740991)
    discovery_ordinal: int = Field(ge=1, le=9007199254740991)
    class_name: str
    first_seen_us: int = Field(ge=0, le=9007199254740991)
    last_seen_us: int = Field(ge=0, le=9007199254740991)
    state: Literal[
        "not_requested", "waiting_evidence", "queued", "processing", "ready", "partial", "failed", "not_applicable"
    ]
    final: bool
    result_revision: int = Field(ge=0, le=9007199254740991)
    evidence_revision: int = Field(ge=0, le=9007199254740991)
    attributes: Attributes
    plate: Plate
    evidence: list[Evidence] = Field(max_length=21)
    expires_at: datetime


class TrackPage(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    job_id: str = Field(pattern="^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
    generation: UUID
    snapshot: int = Field(ge=0, le=9007199254740991)
    items: list[TrackResult] = Field(max_length=100)
    next_cursor: str | None


class VideoJobAccepted(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    job_id: str = Field(pattern="^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
    status: Literal["queued"]
    created_at: datetime


for _model in [
    Error,
    BoundingBox,
    SourceTimeline,
    MediaSource,
    EnrichmentSummary,
    PlaybackState,
    Observation,
    FrameSlice,
    FramePage,
    Attribute,
    Attributes,
    Plate,
    Evidence,
    TrackResult,
    TrackPage,
    VideoJobAccepted,
]:
    _model.model_rebuild()


class VideoExportStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")
    job_id: str
    state: Literal["waiting", "queued", "rendering", "encoding", "ready", "failed"]
    processed_frames: int = Field(ge=0)
    total_frames: int = Field(ge=0)
    expires_at: datetime
    url: str | None
    error_code: str | None
