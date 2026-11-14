from __future__ import annotations

import numpy as np

from app.domain.models import Detection
from app.services.plate_consensus import PlateCandidate, consensus
from app.services.vehicle_cropping import crop_vehicle


def test_vehicle_crop_is_bounded_and_rejects_non_vehicle() -> None:
    image = np.zeros((10, 10, 3), dtype=np.uint8)
    car = Detection(0, "car", .9, -2, 2, 12, 9)
    crop = crop_vehicle(image, car, {"car"})
    assert crop is not None and crop.image.shape[:2] == (7, 10)
    assert crop_vehicle(image, Detection(1, "person", .9, 1, 1, 2, 2), {"car"}) is None
    assert crop_vehicle(image, Detection(0, "car", .9, 12, 1, 14, 2), {"car"}) is None


def test_consensus_never_corrects_or_fabricates_text() -> None:
    candidates = [
        PlateCandidate("PCE7890", .95, .9, 1, 1),
        PlateCandidate("PCE7890", .9, .8, 1, 2),
        PlateCandidate("PCE860", .99, .5, 1, 3),
    ]
    assert consensus(candidates, .8).text == "PCE7890"
    assert consensus([PlateCandidate("PCE7890", .9, .9, 1, 1), PlateCandidate("PCE860", .9, .9, 1, 2)], .8) is None
