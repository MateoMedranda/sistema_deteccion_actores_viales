from datetime import datetime

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
