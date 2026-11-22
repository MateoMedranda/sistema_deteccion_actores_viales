import logging
import pytest
from datetime import UTC,datetime,timedelta
from app.services.video_processing import VideoProcessor,VideoProcessingError
def test_cancel_waits_for_encoder_reap_before_return(tmp_path,monkeypatch):
 events=[]
 class Process:
  pid=0;returncode=None
  def poll(self):return self.returncode
  def terminate(self):events.append("terminate")
  def kill(self):events.append("kill");self.returncode=-9
  def wait(self,timeout=None):
   events.append("wait")
   if timeout:
    import subprocess
    raise subprocess.TimeoutExpired("encoder",timeout)
   self.returncode=-9;return -9
 monkeypatch.setattr("app.services.video_processing.subprocess.Popen",lambda *a,**kw:Process())
 processor=VideoProcessor(None,None,None,"ffmpeg",300,logging.getLogger("test"))
 with pytest.raises(VideoProcessingError):
  processor._encode_h264(tmp_path/"in",tmp_path/"out",lambda:True,expires_at=datetime.now(UTC)+timedelta(seconds=60))
 assert events==["terminate","wait","kill","wait"]
