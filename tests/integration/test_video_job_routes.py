import time

from tests.unit.test_video_job_store import metadata

from tests.video_fixtures import FakeProbe, make_h264_mp4


def _use_fake_probe(client) -> None:
    probe = FakeProbe()
    client.app.state.video_probe = probe
    client.app.state.video_job_service.probe = probe


def test_valid_video_creates_and_completes_job(client, auth_headers, tmp_path) -> None:
    _use_fake_probe(client)
    video = make_h264_mp4(tmp_path / "controlled.mp4")
    started = time.monotonic()
    with video.open("rb") as handle:
        response = client.post("/api/v1/video-jobs", headers=auth_headers, files={"video": ("controlled.mp4", handle, "video/mp4")})
    assert response.status_code == 202
    assert time.monotonic() - started < 2
    job_id = response.json()["job_id"]
    for _ in range(50):
        state = client.get(f"/api/v1/video-jobs/{job_id}", headers=auth_headers).json()
        if state["status"] in {"completed", "failed"}:
            break
        time.sleep(.1)
    assert state["status"] == "completed", state
    page = client.get(f"/api/v1/video-jobs/{job_id}/detections", headers=auth_headers)
    assert page.status_code == 200 and page.json()["total"] > 0
    artifact = client.get(f"/api/v1/video-jobs/{job_id}/annotated-video/content", headers=auth_headers)
    assert artifact.status_code == 200 and artifact.headers["content-type"].startswith("video/mp4")


def test_invalid_video_creates_no_job_or_artifact(client, auth_headers, tmp_path) -> None:
    _use_fake_probe(client)
    response = client.post("/api/v1/video-jobs", headers=auth_headers, files={"video": ("bad.txt", b"not video", "text/plain")})
    assert response.status_code == 415
    assert not list((tmp_path / "video-jobs" / "input").glob("*"))


def test_status_cancel_and_not_ready_routes(client, auth_headers, tmp_path) -> None:
    job = client.app.state.video_jobs.create("default", metadata(), tmp_path / "queued.mp4")
    status = client.get(f"/api/v1/video-jobs/{job.job_id}", headers=auth_headers)
    assert status.status_code == 200 and status.json()["status"] == "queued"
    pending = client.get(f"/api/v1/video-jobs/{job.job_id}/detections", headers=auth_headers)
    assert pending.status_code == 409
    cancelled = client.delete(f"/api/v1/video-jobs/{job.job_id}", headers=auth_headers)
    assert cancelled.status_code == 202 and cancelled.json()["status"] == "cancelled"
    assert client.delete(f"/api/v1/video-jobs/{job.job_id}", headers=auth_headers).status_code == 409
