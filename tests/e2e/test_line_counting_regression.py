from __future__ import annotations

from datetime import UTC, datetime, timedelta

import cv2
import numpy as np
import pytest

from app.domain.models import CountLine, CountPoint, FrameDetection, VideoJob, VideoJobStatus, VideoMetadata
from app.services.count_job_store import CountJobStore
from app.services.count_processing import CountProcessor
from app.services.video_artifacts import VideoArtifactStore


class _VideoStore:
    def __init__(self, source: VideoJob, detections: list[FrameDetection]) -> None:
        self.source, self.detections = source, detections

    def get(self, *_):
        return self.source

    def all_detections(self, *_):
        return self.detections


class _Annotation:
    def render(self, job, source_path, destination, detections, events) -> None:
        destination.write_bytes(b"counted-video")


class _Logger:
    def info(self, *args, **kwargs):
        pass


def _write_video(path) -> None:
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 10, (32, 24))
    writer.write(np.zeros((24, 32, 3), dtype=np.uint8))
    writer.write(np.zeros((24, 32, 3), dtype=np.uint8))
    writer.release()


def _run_count(tmp_path, index: int, start: float, end: float):
    source_path = tmp_path / f"crossing-{index}.mp4"
    _write_video(source_path)
    now = datetime.now(UTC)
    source = VideoJob(
        f"source-{index}", "owner", VideoJobStatus.COMPLETED,
        VideoMetadata("video/mp4", "mp4", "mp4v", 1, .2, 32, 24, 10, 2),
        now, now, now + timedelta(minutes=5), output_path=source_path,
    )

    def detection(frame: int, normalized_y: float) -> FrameDetection:
        center_y = round(normalized_y * 24)
        return FrameDetection(frame, 100 + index, 0, "car", .9, 10, center_y - 2, 20, center_y + 2)

    store = CountJobStore(tmp_path / f"counts-{index}.sqlite3", 3600, 2)
    created = store.create(
        source.job_id, "owner", CountLine(CountPoint(0, .5), CountPoint(1, .5)), 2, source.expires_at,
    )
    claimed = store.dequeue()
    assert claimed is not None
    CountProcessor(
        store, _VideoStore(source, [detection(0, start), detection(1, end)]),
        VideoArtifactStore(tmp_path / f"artifacts-{index}"), _Annotation(), _Logger(),
    ).process(claimed)
    events, total = store.events(created.count_job_id, "owner", 1, 10)
    store.close()
    return events, total


@pytest.mark.parametrize("index,start,end,expected", [
    (1, .2, .8, "A_to_B"), (2, .8, .2, "B_to_A"), (3, .1, .9, "A_to_B"), (4, .9, .1, "B_to_A"),
    (5, .3, .7, "A_to_B"), (6, .7, .3, "B_to_A"), (7, .4, .6, "A_to_B"), (8, .6, .4, "B_to_A"),
    (9, .05, .95, "A_to_B"), (10, .95, .05, "B_to_A"),
])
def test_ten_controlled_videos_count_one_crossing(tmp_path, index: int, start: float, end: float, expected: str) -> None:
    events, total = _run_count(tmp_path, index, start, end)
    assert total == 1 and events[0].direction == expected and events[0].class_name == "car"


def test_controlled_video_without_side_change_has_no_event(tmp_path) -> None:
    events, total = _run_count(tmp_path, 11, .2, .3)
    assert total == 0 and events == []
