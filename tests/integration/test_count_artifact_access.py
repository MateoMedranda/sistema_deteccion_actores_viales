from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.domain.models import CountLine, CountPoint


def test_completed_count_artifact_is_owner_protected(client, auth_headers, tmp_path) -> None:
    count_store = client.app.state.count_jobs
    job = count_store.create(
        "source", "default", CountLine(CountPoint(0, .5), CountPoint(1, .5)), 1,
        datetime.now(UTC) + timedelta(minutes=5),
    )
    assert count_store.dequeue() is not None
    artifact = tmp_path / "counted.mp4"
    artifact.write_bytes(b"not-a-real-video")
    count_store.finish(job.count_job_id, artifact)
    response = client.get(f"/api/v1/count-jobs/{job.count_job_id}/annotated-video", headers=auth_headers)
    assert response.status_code == 200 and response.headers["content-type"].startswith("video/mp4")
    client.app.state.settings.api_keys = "other:other-secret"
    other = client.get(f"/api/v1/count-jobs/{job.count_job_id}/annotated-video", headers={"X-API-Key": "other-secret"})
    assert other.status_code == 404
