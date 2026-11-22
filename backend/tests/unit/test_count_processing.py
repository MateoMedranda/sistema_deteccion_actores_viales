from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.api.error_handlers import ApiError
from app.domain.models import CountLine, CountPoint, FrameDetection, VideoJob, VideoJobStatus, VideoMetadata
from app.services.count_job_store import CountJobStore
from app.services.count_processing import CountProcessor
from app.services.video_artifacts import VideoArtifactStore


class FakeLogger:
    def info(self, *args, **kwargs):
        pass


class FakeVideoStore:
    def __init__(self, source: VideoJob, detections: list[FrameDetection]) -> None:
        self.source, self._detections = source, detections

    def get(self, job_id, owner_key_id):
        return self.source

    def all_detections(self, job_id, owner_key_id):
        return self._detections


class FakeAnnotation:
    def render(self, job, source_path, destination, detections, events) -> None:
        destination.write_bytes(b"temporary-count-video")


def test_processor_uses_persisted_detections_without_detector(tmp_path) -> None:
    output = tmp_path / "source.mp4"
    output.write_bytes(b"source")
    now = datetime.now(UTC)
    source = VideoJob(
        "source", "owner", VideoJobStatus.COMPLETED,
        VideoMetadata("video/mp4", "mp4", "h264", 1, 1, 64, 48, 10, 2),
        now, now, now + timedelta(minutes=5), output_path=output,
    )
    store = CountJobStore(tmp_path / "counts.sqlite3", 3600, 2)
    created = store.create("source", "owner", CountLine(CountPoint(0, .5), CountPoint(1, .5)), 2, source.expires_at)
    job = store.dequeue()
    assert job is not None
    processor = CountProcessor(
        store, FakeVideoStore(source, [
            FrameDetection(0, 1, 0, "car", .9, 10, 4, 30, 14),
            FrameDetection(1, 1, 0, "car", .9, 10, 32, 30, 42),
        ]), VideoArtifactStore(tmp_path / "artifacts"), FakeAnnotation(), FakeLogger(),
    )
    processor.process(job)
    completed = store.get(created.count_job_id, "owner")
    assert completed.status.value == "completed"
    assert [(item.class_name, item.direction, item.total) for item in store.summary(created.count_job_id, "owner")] == [("car", "A_to_B", 1)]
    store.close()


def test_processor_discards_result_when_source_expires_during_count(tmp_path) -> None:
    output = tmp_path / "source.mp4"
    output.write_bytes(b"source")
    now = datetime.now(UTC)
    source = VideoJob(
        "source", "owner", VideoJobStatus.COMPLETED,
        VideoMetadata("video/mp4", "mp4", "h264", 1, 1, 64, 48, 10, 2),
        now, now, now + timedelta(minutes=5), output_path=output,
    )

    class ExpiringVideoStore(FakeVideoStore):
        def __init__(self):
            super().__init__(source, [])
            self.calls = 0

        def get(self, job_id, owner_key_id):
            self.calls += 1
            if self.calls > 1:
                raise ApiError(410, "job_expired", "expired")
            return source

    store = CountJobStore(tmp_path / "counts.sqlite3", 3600, 2)
    created = store.create("source", "owner", CountLine(CountPoint(0, .5), CountPoint(1, .5)), 2, source.expires_at)
    claimed = store.dequeue()
    assert claimed is not None
    processor = CountProcessor(store, ExpiringVideoStore(), VideoArtifactStore(tmp_path / "artifacts"), FakeAnnotation(), FakeLogger())
    from app.services.count_processing import CountProcessingError
    with pytest.raises(CountProcessingError, match="source_expired"):
        processor.process(claimed)
    assert store.events(created.count_job_id, "owner", 1, 10)[1] == 0
    store.close()
