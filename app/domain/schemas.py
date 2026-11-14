from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    code: str
    message: str
    request_id: str


class BoundingBox(BaseModel):
    x_min: int = Field(ge=0)
    y_min: int = Field(ge=0)
    x_max: int = Field(ge=1)
    y_max: int = Field(ge=1)


class DetectionResponseItem(BaseModel):
    detection_id: int = Field(ge=1)
    class_id: int = Field(ge=0)
    class_name: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    bbox: BoundingBox


class ImageMetadata(BaseModel):
    width: int = Field(ge=1)
    height: int = Field(ge=1)
    media_type: str


class AnnotatedImage(BaseModel):
    url: str
    media_type: str = "image/jpeg"
    expires_at: datetime


class DetectionResponse(BaseModel):
    request_id: str
    status: str = "completed"
    processing_time_ms: int = Field(ge=0)
    image: ImageMetadata
    detections: list[DetectionResponseItem]
    annotated_image: AnnotatedImage


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
