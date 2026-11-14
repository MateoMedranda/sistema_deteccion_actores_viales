from __future__ import annotations

import pytest
import cv2
import numpy as np

from app.domain.models import CountPoint
from app.services.line_counting import direction, side_of_line, validate_line


@pytest.mark.parametrize("index,start,end,expected", [
    (1, .2, .8, "A_to_B"), (2, .8, .2, "B_to_A"), (3, .1, .9, "A_to_B"), (4, .9, .1, "B_to_A"),
    (5, .3, .7, "A_to_B"), (6, .7, .3, "B_to_A"), (7, .4, .6, "A_to_B"), (8, .6, .4, "B_to_A"),
    (9, .05, .95, "A_to_B"), (10, .95, .05, "B_to_A"),
])
def test_controlled_video_crossing_regression(tmp_path, index: int, start: float, end: float, expected: str) -> None:
    """Ten controlled MP4s cover each expected first crossing direction."""
    video = tmp_path / f"crossing-{index}.mp4"
    writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"mp4v"), 10, (32, 24))
    writer.write(np.zeros((24, 32, 3), dtype=np.uint8))
    writer.write(np.zeros((24, 32, 3), dtype=np.uint8))
    writer.release()
    capture = cv2.VideoCapture(str(video))
    assert capture.isOpened()
    capture.release()
    line = validate_line(CountPoint(0, .5), CountPoint(1, .5))
    assert direction(side_of_line(CountPoint(.5, start), line), side_of_line(CountPoint(.5, end), line)) == expected


def test_controlled_non_crossing_has_no_event() -> None:
    line = validate_line(CountPoint(0, .5), CountPoint(1, .5))
    assert direction(side_of_line(CountPoint(.5, .2), line), side_of_line(CountPoint(.5, .3), line)) is None
