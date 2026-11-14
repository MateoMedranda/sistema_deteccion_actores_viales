from __future__ import annotations

import math

from app.api.error_handlers import ApiError
from app.domain.models import CountLine, CountPoint, FrameDetection


def validate_line(point_a: CountPoint, point_b: CountPoint) -> CountLine:
    """Validate a non-degenerate line in normalized video coordinates."""
    values = (point_a.x, point_a.y, point_b.x, point_b.y)
    if any(not math.isfinite(value) or value < 0 or value > 1 for value in values):
        raise ApiError(400, "invalid_count_line", "The count line points must be finite normalized coordinates.")
    if point_a == point_b:
        raise ApiError(400, "invalid_count_line", "The count line points must be distinct.")
    return CountLine(point_a, point_b)


def detection_center(detection: FrameDetection, width: int, height: int) -> CountPoint:
    return CountPoint(
        (detection.x_min + detection.x_max) / (2 * width),
        (detection.y_min + detection.y_max) / (2 * height),
    )


def side_of_line(point: CountPoint, line: CountLine, *, epsilon: float = 1e-9) -> int:
    """Return -1/+1 for either side and 0 only when the point lies on the segment's infinite line."""
    cross = ((line.point_b.x - line.point_a.x) * (point.y - line.point_a.y)
             - (line.point_b.y - line.point_a.y) * (point.x - line.point_a.x))
    if abs(cross) <= epsilon:
        return 0
    return 1 if cross > 0 else -1


def direction(previous_side: int, current_side: int) -> str | None:
    if previous_side == 0 or current_side == 0 or previous_side == current_side:
        return None
    return "A_to_B" if previous_side < current_side else "B_to_A"
