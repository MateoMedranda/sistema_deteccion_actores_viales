"""One bounded background reducer; GETs never initiate reconstruction."""
import logging,threading
from app.services.video_progressive_store import now
from app.api.error_handlers import ApiError
class VideoDetailWorker:
 def __init__(self,store,count):
  self.store,self.count=store,count;self.inventory=None;self.stop=threading.Event();self.thread=threading.Thread(target=self.run,name='video-detail-reducer',daemon=True)
 def start(self):self.thread.start()
 def close(self):self.stop.set();self.thread.join()
 def run(self):
  while not self.stop.wait(.05):
   with self.store.lock:jobs=[r[0] for r in self.store.db.execute('SELECT job FROM p_video WHERE retired=0 AND expires>?',(now().isoformat(),))]
   for job in jobs:
    if self.stop.is_set():break
    try:
     self.count.reduce(job)
     if self.inventory:self.inventory.backfill(job)
    except ApiError:pass
    except Exception:
     logging.getLogger('road_actor_detection').exception('video_detail_reducer_failed',extra={'job_id':job,'error_code':'detail_reducer_failed'})
