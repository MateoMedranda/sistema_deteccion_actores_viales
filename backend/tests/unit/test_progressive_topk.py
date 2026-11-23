from datetime import UTC,datetime,timedelta
from fractions import Fraction
from types import SimpleNamespace
import logging,numpy as np
from app.adapters.timed_video_decoder import TimedFrame
from app.domain.models import Detection
from app.services.video_progressive_store import ProgressiveStore
from app.services.progressive_evidence import ProgressiveEvidence
from app.services.progressive_enrichment import ProgressiveEnrichment
def test_late_best_crops_replace_provisional_without_repeating_evaluations(tmp_path):
 store=ProgressiveStore(tmp_path/"db")
 source=tmp_path/"source";source.write_bytes(b"original")
 store.create("job","owner",source,dict(width=64,height=48,fps=10,duration=1),datetime.now(UTC)+timedelta(minutes=5))
 evidence=ProgressiveEvidence(store,tmp_path/"crops",{"car"},2);evidence.initialize();job=SimpleNamespace(job_id="job")
 calls=[]
 class Processor:
  accept_threshold=.8
  def enrich(self,image,index,**kwargs):
   calls.append(index)
   return dict(status="completed",items=[]),dict(status="read",text="OLD" if index==0 else "NEW",ocr_confidence=.95,localizer_confidence=.95,used_enhancement=False)
 worker=ProgressiveEnrichment(evidence,Processor(),logging.getLogger("test"))
 def publish(i):
  frame=TimedFrame(i,i,Fraction(1,10),i*100000,(i+1)*100000,np.zeros((48,64,3),dtype=np.uint8))
  detection=Detection(0,"car",(i+1)/10,1,1,20,20)
  prepared=evidence.prepare(job,frame,[(detection,1)])
  records=[dict(frame_index=i,start_us=i*100000,end_us=(i+1)*100000,pts=str(i),observations=[dict(track_id=1,class_id=0,class_name="car",confidence=detection.confidence,raw_bbox=dict(x_min=1,y_min=1,x_max=20,y_max=20),display_bbox=None)])]
  store.publish("job",records,on_publish=lambda:evidence.commit(job,prepared,records))
 def evaluate():
  record=worker.claim()
  if record:worker.evaluate(record);worker.dirty.add("job");worker.refresh()
  return record
 publish(0);assert evaluate()
 for i in range(1,5):publish(i)
 assert worker.claim() is None
 store.finish_analysis("job")
 while evaluate():pass
 unit=evidence.track("job","owner",1)
 assert unit["final"] is True
 assert [e["frame_index"] for e in unit["evidence"]]==[4,3]
 assert unit["plate"]["text"]=="NEW"
 assert sorted(calls)==[0,3,4]
 for _ in range(5):evidence.track("job","owner",1);store.snapshot("job","owner")
 assert len(calls)==3
 store.close()
