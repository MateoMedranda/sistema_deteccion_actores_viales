from __future__ import annotations

from datetime import UTC, datetime, timedelta

import cv2
import numpy as np

from app.domain.models import CountEvent, CountJob, CountJobStatus, CountLine, CountPoint
from app.services.count_annotation_service import CountAnnotationService


def test_annotation_renders_line_and_counters(tmp_path) -> None:
    source = tmp_path / "source.mp4"
    writer = cv2.VideoWriter(str(source), cv2.VideoWriter_fourcc(*"mp4v"), 10, (32, 24))
    for _ in range(2):
        writer.write(np.zeros((24, 32, 3), dtype=np.uint8))
    writer.release()
    now = datetime.now(UTC)
    job = CountJob(
        "count", "source", "owner", CountJobStatus.PROCESSING,
        CountLine(CountPoint(0, .5), CountPoint(1, .5)), now, now, now + timedelta(minutes=1), 2,
    )
    destination = tmp_path / "counted.mp4"
    CountAnnotationService().render(
        job, source, destination, [], [CountEvent("count", 1, 0, "car", "A_to_B", 1, .1)],
    )
    capture = cv2.VideoCapture(str(destination))
    assert destination.is_file() and capture.isOpened()
    ok, frame = capture.read()
    capture.release()
    assert ok and int(frame.sum()) > 0
