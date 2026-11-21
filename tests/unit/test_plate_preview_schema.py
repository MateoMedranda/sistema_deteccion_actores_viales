import pytest
from pydantic import ValidationError
from app.domain.schemas import PlatePreviewMetadata
def metadata():
 return dict(version=1,source_id="s",enrichment_job_id="j",detection_id=1,profile_id="display-contrast-v1",input_size=dict(width=20,height=10),output_size=dict(width=80,height=40),original_bbox=dict(x_min=0,y_min=0,x_max=20,y_max=10),applied_steps=["grayscale","resize_integer","clahe"],original_to_processed=[4,0,0,0,4,0],expires_at="2030-01-01T00:00:00Z")
def test_strict_metadata_rejects_extra_transform_geometry_and_naive_expiry():
 assert PlatePreviewMetadata(**metadata()).output_size.width==80
 for patch in ({"extra":True},{"original_to_processed":[4,0,1,0,4,0]},{"output_size":{"width":79,"height":40}},{"expires_at":"2030-01-01T00:00:00"},{"detection_id":True}):
  with pytest.raises(ValidationError):PlatePreviewMetadata(**{**metadata(),**patch})
