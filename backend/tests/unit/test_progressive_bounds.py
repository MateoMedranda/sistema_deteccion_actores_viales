import pytest
from pydantic import ValidationError
from app.domain.progressive import BoundingBox, FrameSlice


def test_boxes_and_pts_reject_invalid_geometry_and_64bit_overflow():
    with pytest.raises(ValidationError):
        BoundingBox(x_min=10, y_min=0, x_max=5, y_max=3)
    for pts in (str(2**63), str(-(2**63) - 1)):
        with pytest.raises(ValidationError):
            FrameSlice(
                frame_index=0,
                start_us=0,
                end_us=1,
                pts=pts,
                observation_offset=0,
                observation_total=0,
                observations=[],
            )
