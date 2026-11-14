from app.domain.models import VideoJobStatus
from app.services.video_job_store import VideoJobStore
from tests.unit.test_video_job_store import metadata


def test_nonexpired_processing_job_recovers_after_restart(tmp_path) -> None:
    path = tmp_path / "recovery.sqlite3"
    original = VideoJobStore(path, 3600, 2)
    job = original.create("default", metadata(), tmp_path / "input.mp4")
    assert original.dequeue() is not None
    original.close()
    restored = VideoJobStore(path, 3600, 2)
    assert restored.get(job.job_id, "default").status is VideoJobStatus.QUEUED
    restored.close()
