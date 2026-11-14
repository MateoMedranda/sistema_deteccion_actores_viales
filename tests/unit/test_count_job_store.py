from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.api.error_handlers import ApiError
from app.domain.models import CountEvent, CountLine, CountPoint
from app.services.count_job_store import CountJobStore


def test_count_store_deduplicates_events_and_aggregates(tmp_path) -> None:
    store = CountJobStore(tmp_path / "counts.sqlite3", 3600, 2)
    job = store.create("source", "owner", CountLine(CountPoint(0, .5), CountPoint(1, .5)), 10, datetime.now(UTC) + timedelta(hours=1))
    assert store.dequeue() is not None
    event = CountEvent(job.count_job_id, 7, 0, "car", "A_to_B", 4, .4)
    assert store.record_event(event)
    assert not store.record_event(event)
    store.progress(job.count_job_id, 4)
    events, total = store.events(job.count_job_id, "owner", 1, 20)
    assert total == 1 and events == [event]
    assert store.summary(job.count_job_id, "owner")[0].total == 1
    store.close()


def test_finish_refuses_cancelled_or_expired_job(tmp_path) -> None:
    store = CountJobStore(tmp_path / "counts.sqlite3", 3600, 2)
    line = CountLine(CountPoint(0, .5), CountPoint(1, .5))
    active = store.create("source", "owner", line, 1, datetime.now(UTC) + timedelta(hours=1))
    assert store.dequeue() is not None
    assert store.cancel(active.count_job_id, "owner").status.value == "cancelled"
    assert not store.finish(active.count_job_id, tmp_path / "cancelled.mp4")
    expiring = store.create("source-2", "owner", line, 1, datetime.now(UTC) + timedelta(hours=1))
    assert store.dequeue() is not None
    store._connection.execute(
        "UPDATE count_jobs SET expires_at=? WHERE count_job_id=?",
        ((datetime.now(UTC) - timedelta(seconds=1)).isoformat(), expiring.count_job_id),
    )
    store._connection.commit()
    assert not store.finish(expiring.count_job_id, Path(tmp_path / "expired.mp4"))
    with pytest.raises(ApiError) as error:
        store.get(expiring.count_job_id, "owner")
    assert error.value.status_code == 410
    store.close()
