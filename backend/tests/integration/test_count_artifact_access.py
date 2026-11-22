from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.domain.models import CountEvent, CountLine, CountPoint


def test_completed_count_artifact_is_owner_protected(client, auth_headers, tmp_path) -> None:
    client.app.state.count_worker.close()
    count_store = client.app.state.count_jobs
    job = count_store.create(
        "source", "default", CountLine(CountPoint(0, .5), CountPoint(1, .5)), 1,
        datetime.now(UTC) + timedelta(minutes=5),
    )
    assert count_store.dequeue() is not None
    artifact = tmp_path / "counted.mp4"
    artifact.write_bytes(b"not-a-real-video")
    assert count_store.finish(job.count_job_id, artifact)
    response = client.get(f"/api/v1/count-jobs/{job.count_job_id}/annotated-video", headers=auth_headers)
    assert response.status_code == 200 and response.headers["content-type"].startswith("video/mp4")
    client.app.state.settings.api_keys = "other:other-secret"
    other = client.get(f"/api/v1/count-jobs/{job.count_job_id}/annotated-video", headers={"X-API-Key": "other-secret"})
    assert other.status_code == 404


def test_cancelled_count_has_no_partial_events_or_artifact(client, auth_headers, tmp_path) -> None:
    client.app.state.count_worker.close()
    count_store = client.app.state.count_jobs
    job = count_store.create(
        "source", "default", CountLine(CountPoint(0, .5), CountPoint(1, .5)), 1,
        datetime.now(UTC) + timedelta(minutes=5),
    )
    assert count_store.dequeue() is not None
    assert count_store.record_event(CountEvent(job.count_job_id, 1, 0, "car", "A_to_B", 0, 0))
    assert count_store.cancel(job.count_job_id, "default").status.value == "cancelled"
    events = client.get(f"/api/v1/count-jobs/{job.count_job_id}/events", headers=auth_headers)
    artifact = client.get(f"/api/v1/count-jobs/{job.count_job_id}/annotated-video", headers=auth_headers)
    assert events.status_code == 200 and events.json()["total"] == 0
    assert artifact.status_code == 404


def test_expired_count_job_returns_gone(client, auth_headers) -> None:
    client.app.state.count_worker.close()
    count_store = client.app.state.count_jobs
    job = count_store.create(
        "source", "default", CountLine(CountPoint(0, .5), CountPoint(1, .5)), 1,
        datetime.now(UTC) + timedelta(minutes=5),
    )
    count_store._connection.execute(
        "UPDATE count_jobs SET expires_at=? WHERE count_job_id=?",
        ((datetime.now(UTC) - timedelta(seconds=1)).isoformat(), job.count_job_id),
    )
    count_store._connection.commit()
    response = client.get(f"/api/v1/count-jobs/{job.count_job_id}", headers=auth_headers)
    assert response.status_code == 410
