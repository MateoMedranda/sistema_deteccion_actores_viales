from app.services.video_job_store import VideoJobStore
from tests.unit.test_video_job_store import metadata
from tests.fixtures_008 import Clock
def test_cancel_or_expiry_cannot_publish_output_or_detections(tmp_path):
 for outcome in ("cancel","expire"):
  clock=Clock();s=VideoJobStore(tmp_path/(outcome+".db"),60,2,clock=clock);j=s.create("owner",metadata(),tmp_path/"input");s.dequeue()
  if outcome=="cancel":s.cancel(j.job_id,"owner")
  else:clock.advance(61)
  assert s.finish(j.job_id,tmp_path/"output",[],actual_frame_count=3)!="completed"
  assert s._connection.execute("select count(*) from video_detections").fetchone()[0]==0
  s.close()
