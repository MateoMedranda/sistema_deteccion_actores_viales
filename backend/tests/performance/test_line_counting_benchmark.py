from __future__ import annotations

from datetime import UTC, datetime, timedelta
from time import perf_counter
from statistics import quantiles

import psutil

from app.domain.models import CountLine, CountPoint, FrameDetection, VideoJob, VideoJobStatus, VideoMetadata
from app.services.count_job_store import CountJobStore
from app.services.count_processing import CountProcessor
from app.services.line_counting import side_of_line, validate_line
from app.services.video_artifacts import VideoArtifactStore
from tests.unit.test_video_job_store import metadata


def test_line_geometry_is_fast_and_performs_no_inference() -> None:
    line = validate_line(CountPoint(0, .5), CountPoint(1, .5))
    started = perf_counter()
    for _ in range(10_000):
        side_of_line(CountPoint(.5, .2), line)
    assert perf_counter() - started < 2


class _VideoStore:
    def __init__(self, source, detections):
        self.source, self.detections = source, detections

    def get(self, *_):
        return self.source

    def all_detections(self, *_):
        return self.detections


class _Annotation:
    def render(self, job, source_path, destination, detections, events):
        destination.write_bytes(b"count")


class _Logger:
    def info(self, *args, **kwargs):
        pass


def test_count_processor_meets_small_controlled_budget_without_detector(tmp_path) -> None:
    now = datetime.now(UTC)
    source_path = tmp_path / "source.mp4"
    source_path.write_bytes(b"source")
    source = VideoJob(
        "source", "owner", VideoJobStatus.COMPLETED,
        VideoMetadata("video/mp4", "mp4", "h264", 1, 1, 64, 48, 30, 120),
        now, now, now + timedelta(minutes=5), output_path=source_path,
    )
    detections = [
        FrameDetection(frame, 1, 0, "car", .9, 10, 4 if frame < 60 else 32, 30, 14 if frame < 60 else 42)
        for frame in range(120)
    ]
    store = CountJobStore(tmp_path / "counts.sqlite3", 3600, 2)
    created = store.create("source", "owner", CountLine(CountPoint(0, .5), CountPoint(1, .5)), 120, source.expires_at)
    claimed = store.dequeue()
    assert claimed is not None
    started, before_memory = perf_counter(), psutil.Process().memory_info().rss
    CountProcessor(
        store, _VideoStore(source, detections), VideoArtifactStore(tmp_path / "artifacts"), _Annotation(), _Logger(),
    ).process(claimed)
    elapsed = perf_counter() - started
    memory_growth = psutil.Process().memory_info().rss - before_memory
    assert elapsed < 2 and memory_growth < 100 * 1024 * 1024
    assert store.get(created.count_job_id, "owner").status.value == "completed"
    assert store.summary(created.count_job_id, "owner")[0].total == 1
    store.close()


def test_count_job_confirmation_http_p95_is_under_two_seconds(client, auth_headers, tmp_path) -> None:
    """Creation uses stored video metadata only and does not invoke model inference."""
    source = client.app.state.video_jobs.create("default", metadata(), tmp_path / "staged.mp4")
    assert client.app.state.video_jobs.dequeue() is not None
    client.app.state.video_jobs.finish(source.job_id, tmp_path / "source.mp4", [])
    before_memory = psutil.Process().memory_info().rss
    samples: list[float] = []
    for _ in range(10):
        started = perf_counter()
        response = client.post(
            f"/api/v1/video-jobs/{source.job_id}/count-jobs", headers=auth_headers,
            json={"point_a": {"x": 0, "y": .5}, "point_b": {"x": 1, "y": .5}},
        )
        samples.append(perf_counter() - started)
        assert response.status_code == 202
    p95 = quantiles(samples, n=20, method="inclusive")[18]
    assert p95 < 2 and psutil.Process().memory_info().rss - before_memory < 100 * 1024 * 1024
