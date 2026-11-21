import math
import numpy as np
import pytest
from app.domain.models import Detection, FrameDetection
from app.services.image_geometry import clip_box, canonical_detections
from app.services.vehicle_cropping import crop_vehicle

@pytest.mark.parametrize("box,expected", [
    ((-2, 1, 15, 9), (0, 1, 10, 9)),
    ((1.9, 2.9, 9.9, 8.9), (1, 2, 9, 8)),
    ((12, 1, 14, 3), None), ((3, 4, 3, 7), None),
    ((math.nan, 1, 4, 5), None),
])
def test_boxes_are_bounded_and_never_invent_a_pixel(box, expected):
    assert clip_box(*box, 10, 10) == expected

def test_canonical_collection_matches_crops_without_class_renumbering():
    source = [Detection(0, "car", .9, -2, 2, 12, 9),
              Detection(1, "person", .8, 2, 1, 4, 4),
              Detection(0, "car", .9, 12, 1, 14, 2)]
    normalized = canonical_detections(source, 10, 10)
    assert len(normalized) == 2
    crop = crop_vehicle(np.zeros((10, 10, 3), dtype=np.uint8), normalized[0], {"car"})
    assert (crop.x_min, crop.y_min, crop.x_max, crop.y_max) == (0, 2, 10, 9)

def test_video_crop_keeps_existing_valid_geometry():
    detection = FrameDetection(3, 8, 0, "car", .9, 2, 1, 8, 9)
    crop = crop_vehicle(np.zeros((10, 10, 3), dtype=np.uint8), detection, {"car"})
    assert crop.image.shape[:2] == (8, 6)
