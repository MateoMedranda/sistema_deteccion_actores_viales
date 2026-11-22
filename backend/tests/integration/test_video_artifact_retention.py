from pathlib import Path
import pytest
from app.services.video_job_store import VideoJobStore
from app.services.video_job_service import VideoJobService
from app.services.video_artifacts import VideoArtifactStore
from app.api.error_handlers import ApiError
from tests.fixtures_008 import Clock
from tests.unit.test_video_job_store import metadata
def test_get_cleanup_retains_paths_until_worker_closes_and_janitor_removes(tmp_path):
 clock=Clock();store=VideoJobStore(tmp_path/"jobs.db",60,2,clock=clock);artifacts=VideoArtifactStore(tmp_path/"media")
 source=artifacts.staged_input_path();source.write_bytes(b"input")
 job=store.create("owner",metadata(),source);store.dequeue()
 partial=artifacts.annotated_output_path();partial.write_bytes(b"partial");store.register_path(job.job_id,partial)
 service=VideoJobService(None,None,store,artifacts)
 clock.advance(61)
 with pytest.raises(ApiError) as exc:store.get(job.job_id,"owner")
 assert exc.value.status_code==410
 service.cleanup();assert source.exists() and partial.exists()
 store.release(job.job_id);service.cleanup()
 assert not source.exists() and not partial.exists() and not store._purged
 store.close()
