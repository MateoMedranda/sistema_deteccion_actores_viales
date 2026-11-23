from datetime import UTC, datetime, timedelta
from pathlib import Path
import sqlite3
import pytest
from app.api.error_handlers import ApiError
from app.services.video_progressive_store import ProgressiveStore
from app.services.video_job_store import VideoJobStore
from app.domain.models import VideoMetadata
from tests.integration.test_progressive_store import source


def test_atomic_rollback_and_dense_pages(tmp_path):
    store = ProgressiveStore(tmp_path / "db")
    source(store, tmp_path / "media")
    observation = dict(
        track_id=1,
        class_id=0,
        class_name="car",
        confidence=0.9,
        raw_bbox=dict(x_min=0, y_min=0, x_max=10, y_max=10),
        display_bbox=None,
    )
    frame = dict(
        frame_index=0,
        start_us=0,
        end_us=100,
        pts="0",
        observations=[{**observation, "track_id": i + 1} for i in range(1500)],
    )

    def fail():
        raise RuntimeError("commit_fault")

    with pytest.raises(RuntimeError):
        store.publish("job-1", [frame], on_publish=fail)
    assert store.snapshot("job-1", "owner")["available_until_us"] == 0
    store.publish(
        "job-1", [frame, dict(frame_index=1, start_us=100, end_us=200, pts="1", observations=[])]
    )
    cursor = None
    observed = []
    parts = []
    while True:
        page = store.frames("job-1", "owner", 0, 200, 1, cursor)
        assert len(page["frames"]) <= 100
        assert sum(len(f["observations"]) for f in page["frames"]) <= 1000
        parts.extend(page["frames"])
        observed.extend(o["track_id"] for f in page["frames"] for o in f["observations"])
        cursor = page["next_cursor"]
        if not cursor:
            break
    assert observed == list(range(1, 1501))
    assert parts[-1]["frame_index"] == 1 and parts[-1]["observations"] == []
    token = store.frames("job-1", "owner", 0, 200, 1)["next_cursor"]
    with pytest.raises(ApiError):
        store.frames("job-1", "owner", 0, 100, 1, token)
    store.finish_analysis("job-1", "job_timeout")
    assert store.snapshot("job-1", "owner")["analysis_state"] == "partial_failed"
    assert store.frames("job-1", "owner", 0, 200, 1)["frames"]
    store.close()


def test_restart_preserves_progressive_prefix_but_recovers_legacy(tmp_path):
    path = tmp_path / "db"
    legacy = VideoJobStore(path, 3600, 20)
    store = ProgressiveStore(path, legacy)
    media = tmp_path / "input"
    media.write_bytes(b"original")
    metadata = VideoMetadata("video/mp4", "mp4", "h264", 8, 1, 64, 48, 10, 10)
    job = legacy.create("owner", metadata, media)
    legacy.dequeue()
    store.create(
        job.job_id, "owner", media, dict(width=64, height=48, fps=10, duration=1), job.expires_at
    )
    store.set_timeline(job.job_id, store.snapshot(job.job_id, "owner")["timeline"])
    store.publish(
        job.job_id, [dict(frame_index=0, start_us=0, end_us=100000, pts="0", observations=[])]
    )
    other = legacy.create("owner", metadata, media)
    legacy.dequeue()
    legacy.close()
    legacy = VideoJobStore(path, 3600, 20)
    store = ProgressiveStore(path, legacy)
    assert legacy.get(job.job_id, "owner").status.value == "failed"
    assert legacy.get(other.job_id, "owner").status.value == "queued"
    assert store.snapshot(job.job_id, "owner")["available_until_us"] == 100000
    assert store.snapshot(job.job_id, "owner")["analysis_state"] == "partial_failed"
    with pytest.raises(ApiError) as error:
        store.snapshot(job.job_id, "intruder")
    assert error.value.status_code == 404
    legacy.close()


def test_expiry_during_media_stream_stops_reader_then_cleans(tmp_path, monkeypatch):
    from starlette.requests import Request
    from app.services.progressive_media import media
    import asyncio

    store = ProgressiveStore(tmp_path / "db")
    path = tmp_path / "media"
    path.write_bytes(b"a" * 200000)
    source(store, path)
    request = Request(dict(type="http", method="GET", headers=[]))
    response = media(store, "job-1", "owner", path, request)

    async def consume():
        iterator = response.body_iterator
        assert len(await anext(iterator)) == 65536
        store.withdraw("job-1", "owner")
        assert path.exists()  # open file receipt remains until release
        with pytest.raises(StopAsyncIteration):
            await anext(iterator)

    asyncio.run(consume())
    assert store.readers == {}
    store.cleanup()
    assert not path.exists()
    store.close()
