from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator, StrictFloat


class ErrorResponse(BaseModel):
    code: str
    message: str
    request_id: str


class BoundingBox(BaseModel):
    x_min: int = Field(ge=0)
    y_min: int = Field(ge=0)
    x_max: int = Field(ge=1)
    y_max: int = Field(ge=1)


    @model_validator(mode="after")
    def ordered(self):
        if self.x_max <= self.x_min or self.y_max <= self.y_min:
            raise ValueError("invalid_box_order")
        return self


class DetectionResponseItem(BaseModel):
    detection_id: int = Field(ge=1)
    class_id: int = Field(ge=0)
    class_name: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    bbox: BoundingBox
    enrichment_eligible: bool


class ImageMetadata(BaseModel):
    width: int = Field(ge=1)
    height: int = Field(ge=1)
    media_type: str


class AnnotatedImage(BaseModel):
    url: str
    media_type: str = "image/jpeg"
    expires_at: datetime


class OriginalImage(BaseModel):
    url: str
    media_type: Literal["image/png"]
    expires_at: datetime


class DetectionResponse(BaseModel):
    request_id: str
    status: str = "completed"
    processing_time_ms: int = Field(ge=0)
    image: ImageMetadata
    detections: list[DetectionResponseItem]
    annotated_image: AnnotatedImage
    original_image: OriginalImage
    source_expires_at: datetime


class HealthResponse(BaseModel):
    status: str


class VideoJobAccepted(BaseModel):
    job_id: str
    status: Literal["queued"]
    created_at: datetime


class VideoJobResponse(BaseModel):
    job_id: str
    status: Literal["queued", "processing", "completed", "failed", "cancelled"]
    progress_percent: int = Field(ge=0, le=100)
    processed_frames: int = Field(ge=0)
    total_frames: int = Field(ge=1)
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    error: ErrorResponse | None = None


class VideoClassSummary(BaseModel):
    class_name: str
    detections: int = Field(ge=0)


class FrameDetectionResponse(BaseModel):
    frame_index: int = Field(ge=0)
    track_id: int = Field(ge=1)
    class_id: int = Field(ge=0)
    class_name: str
    confidence: float = Field(ge=0, le=1)
    bbox: BoundingBox


class DetectionPage(BaseModel):
    items: list[FrameDetectionResponse]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)


class TemporaryVideo(BaseModel):
    url: str
    media_type: str = "video/mp4"
    expires_at: datetime


class NormalizedPoint(BaseModel):
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)


class CountJobCreateRequest(BaseModel):
    point_a: NormalizedPoint
    point_b: NormalizedPoint


class CountLineResponse(BaseModel):
    point_a: NormalizedPoint
    point_b: NormalizedPoint


class CountJobAccepted(BaseModel):
    count_job_id: str
    status: Literal["queued"]
    created_at: datetime
    expires_at: datetime
    line: CountLineResponse


class CountEventResponse(BaseModel):
    track_id: int = Field(ge=1)
    class_id: int = Field(ge=0)
    class_name: str = Field(min_length=1)
    direction: Literal["A_to_B", "B_to_A"]
    frame_index: int = Field(ge=0)
    video_time_seconds: float = Field(ge=0)


class CountSummaryResponse(BaseModel):
    class_name: str = Field(min_length=1)
    direction: Literal["A_to_B", "B_to_A"]
    total: int = Field(ge=0)


class CountJobResponse(BaseModel):
    count_job_id: str
    source_video_job_id: str
    status: Literal["queued", "processing", "completed", "failed", "cancelled"]
    line: CountLineResponse
    progress_percent: int = Field(ge=0, le=100)
    processed_frames: int = Field(ge=0)
    total_frames: int = Field(ge=1)
    events: list[CountEventResponse]
    summary: list[CountSummaryResponse]
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    error: ErrorResponse | None = None


class CountEventPage(BaseModel):
    items: list[CountEventResponse]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)


class SourceReference(BaseModel):
    kind: Literal["image", "video"]
    source_id: str


class EnrichmentJobCreateRequest(BaseModel):
    source: SourceReference


class EnrichmentJobAccepted(BaseModel):
    enrichment_job_id: str
    status: Literal["queued"]
    created_at: datetime
    expires_at: datetime


class EnrichmentJobResponse(BaseModel):
    enrichment_job_id: str
    source: SourceReference
    status: Literal["queued", "processing", "completed", "failed", "cancelled"]
    processed_units: int = Field(ge=0)
    total_units: int = Field(ge=0)
    progress_percent: int = Field(ge=0, le=100)
    results_ready: int = Field(ge=0)
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    error: ErrorResponse | None = None


class RelativeBoundingBox(BaseModel):
    x_min: float = Field(ge=0, le=1)
    y_min: float = Field(ge=0, le=1)
    x_max: float = Field(ge=0, le=1)
    y_max: float = Field(ge=0, le=1)


    @model_validator(mode="after")
    def ordered(self):
        if self.x_max <= self.x_min or self.y_max <= self.y_min:
            raise ValueError("invalid_box_order")
        return self


class EnrichmentAttribute(BaseModel):
    name: str
    label: str
    confidence: float = Field(ge=0, le=1)
    evidence_frame_index: int | None = Field(default=None, ge=0)



PlateVariant=Literal["raw","legacy-retry-v1","bilateral-clahe-v1","bilateral-adaptive-v1"]
class PlateReadingProvenance(BaseModel):
    model_config={"extra":"forbid"}
    @model_validator(mode="before")
    @classmethod
    def strict_version(cls,value):
        if isinstance(value,dict) and type(value.get("version")) is not int:raise ValueError("invalid_version")
        return value
    version: Literal[1]
    policy_id: Literal["baseline-v1","candidate-rescue-v1","legacy-unknown"]
    attempted_variants: list[PlateVariant]
    selected_variant: Literal["raw","legacy-retry-v1","bilateral-clahe-v1","bilateral-adaptive-v1","none","unknown"]
    @model_validator(mode="after")
    def consistent_origin(self):
        if len(self.attempted_variants)!=len(set(self.attempted_variants)):raise ValueError("duplicate_variant")
        if self.policy_id=="legacy-unknown":
            if self.attempted_variants or self.selected_variant not in ("unknown","none"):raise ValueError("invalid_legacy")
        elif self.selected_variant=="unknown" or (self.selected_variant!="none" and self.selected_variant not in self.attempted_variants):raise ValueError("invalid_selected")
        if self.policy_id=="baseline-v1" and any(v not in ("raw","legacy-retry-v1") for v in self.attempted_variants):raise ValueError("invalid_baseline")
        return self


class EnrichmentPlate(BaseModel):
    status: Literal["read", "unreadable", "not_detected", "failed"]
    bbox_relative: RelativeBoundingBox | None = None
    localizer_confidence: float | None = Field(default=None, ge=0, le=1)
    ocr_confidence: float | None = Field(default=None, ge=0, le=1)
    text: str | None = None
    used_enhancement: bool = False
    provenance: PlateReadingProvenance | None = None
    evidence_frame_indexes: list[int] = []


    @model_validator(mode="after")
    def redact_non_read(self):
        if self.status != "read":
            self.text = None
        if self.status == "not_detected":
            self.bbox_relative = None
        if self.provenance and self.provenance.policy_id!="legacy-unknown":
            if self.status!="read":
                self.provenance.selected_variant="none"
            elif self.provenance.selected_variant not in self.provenance.attempted_variants:
                raise ValueError("missing_read_origin")
        return self


class EnrichedVehicleResult(BaseModel):
    vehicle_key: str
    detection_id: int = Field(ge=1)
    track_id: int | None = Field(default=None, ge=1)
    class_id: int = Field(ge=0)
    class_name: str
    evidence_frame_indexes: list[int] = []
    attributes_status: Literal["completed", "failed"]
    plate_status: Literal["read", "unreadable", "not_detected", "failed"]
    attributes: list[EnrichmentAttribute] = []
    plate: EnrichmentPlate
    error_code: str | None = None


class EnrichedVehiclePage(BaseModel):
    items: list[EnrichedVehicleResult]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)


class EnrichmentCapabilities(BaseModel):
    attributes: Literal["ready", "unavailable"]
    plate_localization: Literal["ready", "unavailable"]
    plate_ocr: Literal["ready", "unavailable"]


class EnrichmentReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    capabilities: EnrichmentCapabilities



class PreviewSize(BaseModel):
    model_config = {"extra":"forbid","strict":True}
    width: int = Field(ge=2,le=2048)
    height: int = Field(ge=2,le=2048)

class PreviewInputSize(BaseModel):
    model_config = {"extra":"forbid","strict":True}
    width: int = Field(ge=2)
    height: int = Field(ge=2)

class PreviewBoundingBox(BoundingBox):
    model_config = {"extra":"forbid","strict":True}

class PlatePreviewMetadata(BaseModel):
    model_config = {"extra":"forbid"}
    @model_validator(mode="before")
    @classmethod
    def strict_version(cls,value):
        if isinstance(value,dict) and type(value.get("version")) is not int:raise ValueError("invalid_version")
        return value
    version: Literal[1]
    source_id: str = Field(min_length=1,max_length=128)
    enrichment_job_id: str = Field(min_length=1,max_length=128)
    detection_id: int = Field(ge=1,strict=True)
    profile_id: Literal["display-contrast-v1"]
    input_size: PreviewInputSize
    output_size: PreviewSize
    original_bbox: PreviewBoundingBox
    applied_steps: list[Literal["grayscale","resize_integer","clahe"]]
    original_to_processed: list[StrictFloat] = Field(min_length=6,max_length=6)
    expires_at: datetime

    @model_validator(mode="after")
    def consistent_preview(self):
        import math
        m=self.original_to_processed;s=m[0]
        b=self.original_bbox
        if not all(math.isfinite(v) for v in m) or s not in (1,2,3,4) or m!=[s,0,0,0,s,0]:raise ValueError("invalid_transform")
        if self.input_size.width!=b.x_max-b.x_min or self.input_size.height!=b.y_max-b.y_min:raise ValueError("invalid_roi_size")
        if self.output_size.width!=self.input_size.width*s or self.output_size.height!=self.input_size.height*s or self.output_size.width*self.output_size.height>2_000_000:raise ValueError("invalid_output_size")
        expected=["grayscale"]+(["resize_integer"] if s>1 else [])+["clahe"]
        if self.applied_steps!=expected:raise ValueError("invalid_steps")
        if self.expires_at.utcoffset() is None or self.expires_at.utcoffset().total_seconds()!=0:raise ValueError("invalid_expiry")
        return self


class ImageUploadPolicy(BaseModel):
    media_types: list[Literal["image/jpeg", "image/png"]]
    max_upload_bytes: int = Field(gt=0)
    max_image_pixels: int = Field(gt=0)
