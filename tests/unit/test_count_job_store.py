from __future__ import annotations

from datetime import UTC, datetime, timedelta

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
