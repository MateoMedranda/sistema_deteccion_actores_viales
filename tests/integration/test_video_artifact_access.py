from app.domain.models import VideoJobStatus
from tests.unit.test_video_job_store import metadata


def test_cancelled_job_has_no_annotated_artifact(client, auth_headers, tmp_path) -> None:
    job = client.app.state.video_jobs.create("default", metadata(), tmp_path / "input.mp4")
    client.app.state.video_jobs.cancel(job.job_id, "default")
    response = client.get(f"/api/v1/video-jobs/{job.job_id}/annotated-video/content", headers=auth_headers)
    assert response.status_code == 404
