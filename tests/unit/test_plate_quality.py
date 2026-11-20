from __future__ import annotations

import numpy as np
import cv2

from app.services.plate_quality import conservative_enhance, rectify_plate


def test_quality_retry_is_non_generative_and_keeps_image_channels() -> None:
    plate = np.full((10, 20, 3), 110, dtype=np.uint8)
    assert conservative_enhance(rectify_plate(plate)).shape[2] == 3


def test_horizontal_plate_is_not_rotated_ninety_degrees() -> None:
    plate = np.zeros((30, 100, 3), dtype=np.uint8)
    cv2.rectangle(plate, (4, 4), (95, 25), (255, 255, 255), 2)
    assert np.array_equal(rectify_plate(plate), plate)


def test_enhancement_enlarges_tiny_plate_without_changing_aspect_ratio() -> None:
    plate = np.full((12, 36, 3), 110, dtype=np.uint8)
    enhanced = conservative_enhance(plate)
    assert enhanced.shape == (12 * 4 + 16, 36 * 4 + 16, 3)
