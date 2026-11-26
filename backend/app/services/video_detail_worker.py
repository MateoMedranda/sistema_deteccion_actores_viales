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
     if hasattr(self,"multiline"):
      try:self.multiline.reduce(job)
      except ApiError:pass
      except Exception:
       with self.store.lock,self.store.db:self.store.db.execute("UPDATE p_count_lines SET error='count_reducer_failed' WHERE job=? AND deleted=0 AND error IS NULL",(job,))
       logging.getLogger('road_actor_detection').exception('count_lines_reducer_failed',extra={'job_id':job})
     self.count.reduce(job)
     if self.inventory:self.inventory.backfill(job)
    except ApiError:pass
    except Exception:
     logging.getLogger('road_actor_detection').exception('video_detail_reducer_failed',extra={'job_id':job,'error_code':'detail_reducer_failed'})
