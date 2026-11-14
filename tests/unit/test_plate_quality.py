from __future__ import annotations

import numpy as np

from app.services.plate_quality import conservative_enhance, rectify_plate


def test_quality_retry_is_non_generative_and_keeps_image_channels() -> None:
    plate = np.full((10, 20, 3), 110, dtype=np.uint8)
    assert conservative_enhance(rectify_plate(plate)).shape[2] == 3
