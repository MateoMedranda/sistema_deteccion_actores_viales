from datetime import UTC,datetime,timedelta
from threading import Event,Thread
from types import SimpleNamespace
import logging
import cv2
import numpy as np
from app.domain.models import Detection
from app.services.enrichment_job_store import EnrichmentJobStore
from app.services.enrichment_worker import EnrichmentWorker

def test_queued_cancel_is_never_dequeued(tmp_path):
    jobs=EnrichmentJobStore(tmp_path/"jobs.sqlite3",60,5)
    job=jobs.create("image","source","owner",1,datetime.now(UTC)+timedelta(seconds=60))
    jobs.cancel(job.enrichment_job_id,"owner")
    assert jobs.dequeue() is None
    assert jobs.get(job.enrichment_job_id,"owner").status.value=="cancelled"
    jobs.close()

def test_worker_returning_after_cancel_does_not_restore_results(tmp_path):
    jobs=EnrichmentJobStore(tmp_path/"jobs.sqlite3",60,5)
    created=jobs.create("image","source","owner",1,datetime.now(UTC)+timedelta(seconds=60))
    job=jobs.dequeue()
    entered,released=Event(),Event()
    detection=Detection(0,"car",.9,0,0,10,10)
    ok,png=cv2.imencode(".png",np.zeros((10,10,3),dtype=np.uint8))
    assert ok
    class Processor:
        accept_threshold=.8
        def enrich(self,*args,**kwargs):
            entered.set()
            assert released.wait(2)
            return ({"status":"completed","items":[]},{"status":"not_detected","used_enhancement":False,"evidence_frame_indexes":[]})
    service=SimpleNamespace(resolve=lambda *a:SimpleNamespace(),units_for_source=lambda *a:[{"bbox":detection,"track_id":None,"detection_id":1,"class_id":0,"class_name":"car","vehicle_key":"detection-1"}],images=SimpleNamespace(read_original=lambda *a:(png.tobytes(),None)),settings=SimpleNamespace(vehicle_class_set=lambda:{"car"}))
    worker=EnrichmentWorker(jobs,service,Processor(),logging.getLogger("test.worker"))
    thread=Thread(target=worker._process,args=(job,))
    thread.start()
    assert entered.wait(2)
    jobs.cancel(created.enrichment_job_id,"owner")
    released.set()
    thread.join(2)
    assert not thread.is_alive()
    assert jobs.get(created.enrichment_job_id,"owner").status.value=="cancelled"
    assert jobs.connection.execute("SELECT results_json FROM enrichment_jobs").fetchone()[0]=="[]"
    assert jobs.connection.execute("SELECT count(*) FROM enrichment_plates").fetchone()[0]==0
    jobs.close()
