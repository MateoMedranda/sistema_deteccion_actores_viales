from datetime import UTC, datetime, timedelta
from pathlib import Path
import pytest
from app.api.error_handlers import ApiError
from app.services.video_progressive_store import ProgressiveStore


def source(store, path):
    return store.create(
        "job-1",
        "owner",
        path,
        {"width": 64, "height": 48, "fps": 10, "duration": 2},
        datetime.now(UTC) + timedelta(minutes=5),
    )


def test_commit_is_contiguous_empty_frames_are_real_and_withdrawal_is_terminal(tmp_path):
    store = ProgressiveStore(tmp_path / "db.sqlite3")
    source(store, tmp_path / "input.mp4")
    frame = {"frame_index": 0, "start_us": 0, "end_us": 100000, "pts": "0", "observations": []}
    store.publish("job-1", [frame])
    assert store.snapshot("job-1", "owner")["available_until_us"] == 100000
    store.publish("job-1", [frame])
    assert store.snapshot("job-1", "owner")["revision"] == 1
    with pytest.raises(ValueError):
        store.publish("job-1", [{**frame, "frame_index": 2, "start_us": 200000, "end_us": 300000}])
    with pytest.raises(ApiError):
        store.snapshot("job-1", "other")
    store.withdraw("job-1", "owner")
    with pytest.raises(ApiError):
        store.snapshot("job-1", "owner")
    with pytest.raises(ApiError):
        store.publish("job-1", [{**frame, "frame_index": 1, "start_us": 100000, "end_us": 200000}])
    store.close()
