from app.services.video_job_store import VideoJobStore
from tests.unit.test_video_job_store import metadata
def test_confirmed_actual_count_and_encoding_are_not_completed(tmp_path):
 s=VideoJobStore(tmp_path/"jobs.sqlite3",3600,2);j=s.create("owner",metadata(),tmp_path/"in.mp4");s.dequeue()
 s.confirm_frames(j.job_id,3)
 job=s.get(j.job_id,"owner")
 assert job.status.value=="processing" and job.processing_phase=="encoding"
 assert job.processed_frames==job.metadata.total_frames==3 and job.frame_total_confirmed
 assert job.video_metadata is None
 assert s.finish(j.job_id,tmp_path/"out.mp4",[],actual_frame_count=3,eligible_classes={"car"})=="completed"
 result=s.get(j.job_id,"owner")
 assert result.processing_phase=="ready" and result.video_metadata["frame_count"]==3 and result.eligible_track_count==0
 s.close()
