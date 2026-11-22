from __future__ import annotations

import pytest

from app.api.error_handlers import ApiError
from app.domain.models import CountPoint, FrameDetection
from app.services.line_counting import detection_center, direction, side_of_line, validate_line


def test_line_validation_and_side_direction() -> None:
    line = validate_line(CountPoint(0, .5), CountPoint(1, .5))
    assert side_of_line(CountPoint(.5, .2), line) == -1
    assert side_of_line(CountPoint(.5, .8), line) == 1
    assert side_of_line(CountPoint(.5, .5), line) == 0
    assert direction(-1, 1) == "A_to_B"
    assert direction(1, -1) == "B_to_A"
    assert direction(-1, 0) is None


@pytest.mark.parametrize("left,right", [(CountPoint(-.1, .2), CountPoint(.1, .2)), (CountPoint(.2, .2), CountPoint(.2, .2))])
def test_invalid_line_is_rejected(left: CountPoint, right: CountPoint) -> None:
    with pytest.raises(ApiError) as error:
        validate_line(left, right)
    assert error.value.status_code == 400


def test_detection_center_is_normalized() -> None:
    detection = FrameDetection(0, 1, 0, "car", .9, 10, 20, 30, 40)
    assert detection_center(detection, 40, 80) == CountPoint(.5, .375)
