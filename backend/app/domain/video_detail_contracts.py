"""Typed additive response contracts generated from reviewed 010 schemas."""
from __future__ import annotations
from datetime import datetime
from uuid import UUID
from typing import Annotated,Literal
from pydantic import BaseModel,ConfigDict,Field
class Contract(BaseModel):
 model_config=ConfigDict(extra='forbid',allow_inf_nan=False)

class Point(Contract):
 x: Annotated[float,Field(ge=0,le=1,strict=True)]
 y: Annotated[float,Field(ge=0,le=1,strict=True)]

class Line(Contract):
 point_a: Point
 point_b: Point

class Box(Contract):
 x_min: Annotated[int,Field(ge=0,le=9007199254740991,strict=True)]
 y_min: Annotated[int,Field(ge=0,le=9007199254740991,strict=True)]
 x_max: Annotated[int,Field(ge=1,le=9007199254740991,strict=True)]
 y_max: Annotated[int,Field(ge=1,le=9007199254740991,strict=True)]

class Capabilities(Contract):
 job_id: Annotated[str,Field(pattern='^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$')]
 generation: UUID
 protocol: Literal['video-detail-v1']
 temporal_inspection: Literal['supported', 'unavailable']
 directed_count: Literal['supported', 'unavailable']
 detection_summary: Literal['building', 'supported', 'unavailable']
 label_export: Literal['supported', 'unavailable']
 reason_codes: Annotated[list[Annotated[str,Field(pattern='^[a-z0-9_]{1,64}$')]],Field(max_length=20)]
 expires_at: datetime

class InspectionRequest(Contract):
 generation: UUID
 track_id: Annotated[int,Field(ge=1,le=9007199254740991,strict=True)]
 frame_index: Annotated[int,Field(ge=0,le=9007199254740991,strict=True)]

class Asset(Contract):
 asset_id: UUID
 kind: Literal['vehicle', 'plate']
 url: Annotated[str,Field(pattern='^/api/v1/video-jobs/[A-Za-z0-9][A-Za-z0-9_-]{0,127}/playback/')]
 expires_at: datetime

class Attribute(Contract):
 name: Annotated[str,Field(max_length=128)]
 value: Annotated[str,Field(max_length=256)]
 confidence: Annotated[float,Field(ge=0,le=1,strict=True)]
 inspection_id: UUID

class Attributes(Contract):
 status: Literal['pending', 'completed', 'partial', 'failed', 'not_applicable']
 items: Annotated[list[Attribute],Field(max_length=20)]
 error_code: Annotated[str,Field(pattern='^[a-z0-9_]{1,64}$')] | None

class Plate(Contract):
 status: Literal['pending', 'read', 'unreadable', 'not_detected', 'failed', 'not_applicable']
 text: Annotated[str,Field(max_length=128)] | None
 ocr_confidence: Annotated[float,Field(ge=0,le=1,strict=True)] | None
 inspection_id: UUID
 policy_id: Annotated[str,Field(max_length=128)]
 used_enhancement: Annotated[bool,Field(strict=True)]
 error_code: Annotated[str,Field(pattern='^[a-z0-9_]{1,64}$')] | None

class Inspection(Contract):
 job_id: Annotated[str,Field(pattern='^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$')]
 generation: UUID
 inspection_id: UUID
 policy_version: Literal['selected-frame-v1']
 track_id: Annotated[int,Field(ge=1,le=9007199254740991,strict=True)]
 frame_index: Annotated[int,Field(ge=0,le=9007199254740991,strict=True)]
 time_us: Annotated[int,Field(ge=0,le=9007199254740991,strict=True)]
 end_us: Annotated[int,Field(ge=1,le=9007199254740991,strict=True)]
 class_name: Annotated[str,Field(max_length=256)]
 bbox: Box
 observation_kind: Literal['measured', 'predicted']
 state: Literal['queued', 'preparing', 'processing', 'ready', 'partial', 'unavailable', 'failed', 'not_applicable']
 result_revision: Annotated[int,Field(ge=0,le=9007199254740991,strict=True)]
 vehicle: Asset | None
 plate_asset: Asset | None
 attributes: Attributes
 plate: Plate
 plate_preview_url: Annotated[str,Field(pattern='^/api/v1/video-jobs/[A-Za-z0-9][A-Za-z0-9_-]{0,127}/playback/')] | None
 plate_preview_profiles: Annotated[list[str],Field(max_length=10)]
 error_code: Annotated[str,Field(pattern='^[a-z0-9_]{1,64}$')] | None
 expires_at: datetime
 confidence: Annotated[float,Field(ge=0,le=1,strict=True)]
 confidence_kind: Literal['measured', 'last_measured']

class DirectedCountRequest(Contract):
 generation: UUID
 expected_revision: Annotated[int,Field(ge=0,le=9007199254740991,strict=True)]
 line: Line
 direction: Literal['negative_to_positive', 'positive_to_negative']

class DirectedCount(Contract):
 job_id: Annotated[str,Field(pattern='^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$')]
 generation: UUID
 policy_version: Literal['finite-center-v1']
 revision: Annotated[int,Field(ge=0,le=9007199254740991,strict=True)]
 enabled: Annotated[bool,Field(strict=True)]
 line: Line | None
 direction: Literal['negative_to_positive', 'positive_to_negative'] | None
 status: Literal['disabled', 'pending', 'ready', 'unavailable']
 at_us: Annotated[int,Field(ge=0,le=9007199254740991,strict=True)]
 available_until_us: Annotated[int,Field(ge=0,le=9007199254740991,strict=True)]
 covered_until_us: Annotated[int,Field(ge=0,le=9007199254740991,strict=True)]
 total: Annotated[int,Field(ge=0,le=9007199254740991,strict=True)] | None
 error_code: Annotated[str,Field(pattern='^[a-z0-9_]{1,64}$')] | None
 expires_at: datetime

class SummaryClass(Contract):
 class_key: Annotated[str,Field(max_length=256)]
 label: Annotated[str,Field(max_length=256)]
 color: Annotated[str,Field(pattern='^#[0-9A-Fa-f]{6}$')]
 track_count: Annotated[int,Field(ge=1,le=9007199254740991,strict=True)]
 requires_review: Annotated[bool,Field(strict=True)]

class DetectionSummary(Contract):
 job_id: Annotated[str,Field(pattern='^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$')]
 generation: UUID
 policy_version: Literal['vehicle-inventory-v1']
 status: Literal['building', 'partial', 'final', 'unavailable']
 revision: Annotated[int,Field(ge=0,le=9007199254740991,strict=True)]
 covered_frames: Annotated[int,Field(ge=0,le=9007199254740991,strict=True)]
 covered_until_us: Annotated[int,Field(ge=0,le=9007199254740991,strict=True)]
 available_until_us: Annotated[int,Field(ge=0,le=9007199254740991,strict=True)]
 analysis_complete: Annotated[bool,Field(strict=True)]
 total_tracks: Annotated[int,Field(ge=0,le=9007199254740991,strict=True)] | None
 classes: Annotated[list[SummaryClass],Field(max_length=1000)]
 excluded_nonvehicle_tracks: Annotated[int,Field(ge=0,le=9007199254740991,strict=True)]
 requires_review: Annotated[bool,Field(strict=True)]
 error_code: Annotated[str,Field(pattern='^[a-z0-9_]{1,64}$')] | None
 expires_at: datetime

class LabelExportStatus(Contract):
 job_id: Annotated[str,Field(pattern='^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$')]
 renderer_version: Literal['vehicle-labels-v1']
 state: Literal['waiting', 'queued', 'rendering', 'encoding', 'ready', 'failed']
 processed_frames: Annotated[int,Field(ge=0,le=9007199254740991,strict=True)]
 total_frames: Annotated[int,Field(ge=0,le=9007199254740991,strict=True)]
 expires_at: datetime
 url: Annotated[str,Field(pattern='^/api/v1/video-jobs/[A-Za-z0-9][A-Za-z0-9_-]{0,127}/playback/')] | None
 error_code: Annotated[str,Field(pattern='^[a-z0-9_]{1,64}$')] | None

class InspectionPlatePreviewMetadata(Contract):
 version: Literal['inspection-plate-preview-v1']
 inspection_id: UUID
 plate_asset_id: UUID
 job_id: Annotated[str,Field(pattern='^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$')]
 generation: UUID
 track_id: Annotated[int,Field(ge=1,le=9007199254740991,strict=True)]
 frame_index: Annotated[int,Field(ge=0,le=9007199254740991,strict=True)]
 time_us: Annotated[int,Field(ge=0,le=9007199254740991,strict=True)]
 coordinate_space: Literal['plate-crop']
 original_width: Annotated[int,Field(ge=1,le=9007199254740991,strict=True)]
 original_height: Annotated[int,Field(ge=1,le=9007199254740991,strict=True)]
 processed_width: Annotated[int,Field(ge=1,le=9007199254740991,strict=True)]
 processed_height: Annotated[int,Field(ge=1,le=9007199254740991,strict=True)]
 source_to_processed: Annotated[list[Annotated[float,Field(strict=True)]],Field(min_length=6,max_length=6)]
 profile_id: Annotated[str,Field(max_length=128)]
 policy_version: Annotated[str,Field(max_length=128)]
 display_only: Literal[True]
 expires_at: datetime

Point.model_rebuild()
Line.model_rebuild()
Box.model_rebuild()
Capabilities.model_rebuild()
InspectionRequest.model_rebuild()
Asset.model_rebuild()
Attribute.model_rebuild()
Attributes.model_rebuild()
Plate.model_rebuild()
Inspection.model_rebuild()
DirectedCountRequest.model_rebuild()
DirectedCount.model_rebuild()
SummaryClass.model_rebuild()
DetectionSummary.model_rebuild()
LabelExportStatus.model_rebuild()
InspectionPlatePreviewMetadata.model_rebuild()
