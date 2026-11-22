from pathlib import Path

import pytest

from app.api.error_handlers import ApiError
from app.domain.models import FrameDetection, VideoJobStatus, VideoMetadata
from app.services.video_job_store import VideoJobStore


def metadata() -> VideoMetadata:
    return VideoMetadata("video/mp4", "mov,mp4,m4a,3gp,3g2,mj2", "h264", 10, 1.0, 16, 16, 10.0, 10)


def test_job_lifecycle_and_paginated_detections(tmp_path: Path) -> None:
    store = VideoJobStore(tmp_path / "jobs.sqlite3", 3600, 2)
    created = store.create("default", metadata(), tmp_path / "input.mp4")
    claimed = store.dequeue()
    assert claimed is not None and claimed.status is VideoJobStatus.PROCESSING
    store.progress(created.job_id, 3)
    store.finish(created.job_id, tmp_path / "output.mp4", [
        FrameDetection(0, 1, 0, "car", .9, 0, 0, 5, 5),
        FrameDetection(1, 1, 0, "car", .8, 1, 1, 6, 6),
    ])
    assert store.get(created.job_id, "default").status is VideoJobStatus.COMPLETED
    rows, total = store.detections(created.job_id, "default", page=1, page_size=1)
    assert total == 2 and rows[0].frame_index == 0
    assert store.summary(created.job_id, "default") == {"car": 2}
    store.close()


def test_cancelled_job_cannot_be_claimed_or_recancelled(tmp_path: Path) -> None:
    store = VideoJobStore(tmp_path / "jobs.sqlite3", 3600, 2)
    created = store.create("default", metadata(), tmp_path / "input.mp4")
    assert store.cancel(created.job_id, "default").status is VideoJobStatus.CANCELLED
    assert store.dequeue() is None
    with pytest.raises(ApiError) as error:
        store.cancel(created.job_id, "default")
    assert error.value.status_code == 409
    store.close()


def test_processing_job_is_requeued_on_restart(tmp_path: Path) -> None:
    path = tmp_path / "jobs.sqlite3"
    store = VideoJobStore(path, 3600, 2)
    created = store.create("default", metadata(), tmp_path / "input.mp4")
    assert store.dequeue() is not None
    store.close()
    restarted = VideoJobStore(path, 3600, 2)
    assert restarted.get(created.job_id, "default").status is VideoJobStatus.QUEUED
    restarted.close()


def test_failed_processing_and_owner_isolation(tmp_path: Path) -> None:
    store = VideoJobStore(tmp_path / "jobs.sqlite3", 3600, 2)
    created = store.create("north", metadata(), tmp_path / "input.mp4")
    assert store.dequeue() is not None
    store.fail(created.job_id, "processing_failed")
    assert store.get(created.job_id, "north").status is VideoJobStatus.FAILED
    with pytest.raises(ApiError) as invisible:
        store.get(created.job_id, "south")
    assert invisible.value.status_code == 404
    with pytest.raises(ApiError) as terminal:
        store.cancel(created.job_id, "north")
    assert terminal.value.status_code == 409
    store.close()
