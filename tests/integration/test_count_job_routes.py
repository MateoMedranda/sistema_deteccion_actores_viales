from __future__ import annotations

import time

from app.domain.models import FrameDetection
from tests.unit.test_video_job_store import metadata
from tests.video_fixtures import make_h264_mp4


def _completed_source(client, tmp_path):
    source_video = make_h264_mp4(tmp_path / "source.mp4")
    job = client.app.state.video_jobs.create("default", metadata(), tmp_path / "staged.mp4")
    assert client.app.state.video_jobs.dequeue() is not None
    client.app.state.video_jobs.finish(job.job_id, source_video, [
        FrameDetection(0, 11, 0, "car", .9, 10, 4, 30, 14),
        FrameDetection(1, 11, 0, "car", .9, 10, 32, 30, 42),
    ])
    return job


def test_count_job_reports_one_directional_event(client, auth_headers, tmp_path) -> None:
    source = _completed_source(client, tmp_path)
    response = client.post(
        f"/api/v1/video-jobs/{source.job_id}/count-jobs", headers=auth_headers,
        json={"point_a": {"x": 0, "y": .5}, "point_b": {"x": 1, "y": .5}},
    )
    assert response.status_code == 202
    count_id = response.json()["count_job_id"]
    for _ in range(50):
        status = client.get(f"/api/v1/count-jobs/{count_id}", headers=auth_headers)
        if status.json()["status"] in {"completed", "failed", "cancelled"}:
            break
        time.sleep(.05)
    assert status.json()["status"] == "completed", status.json()
    assert status.json()["summary"] == [{"class_name": "car", "direction": "A_to_B", "total": 1}]
    events = client.get(f"/api/v1/count-jobs/{count_id}/events", headers=auth_headers)
    assert events.status_code == 200 and events.json()["total"] == 1
    artifact = client.get(f"/api/v1/count-jobs/{count_id}/annotated-video", headers=auth_headers)
    assert artifact.status_code == 200 and artifact.headers["content-type"].startswith("video/mp4")


def test_count_job_rejects_invalid_line_and_other_owner(client, auth_headers, tmp_path) -> None:
    source = _completed_source(client, tmp_path)
    invalid = client.post(
        f"/api/v1/video-jobs/{source.job_id}/count-jobs", headers=auth_headers,
        json={"point_a": {"x": .5, "y": .5}, "point_b": {"x": .5, "y": .5}},
    )
    assert invalid.status_code == 400
    client.app.state.settings.api_keys = "other:other-secret"
    inaccessible = client.post(
        f"/api/v1/video-jobs/{source.job_id}/count-jobs", headers={"X-API-Key": "other-secret"},
        json={"point_a": {"x": 0, "y": .5}, "point_b": {"x": 1, "y": .5}},
    )
    assert inaccessible.status_code == 404
