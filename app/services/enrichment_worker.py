from __future__ import annotations
import threading
import cv2
import numpy as np
from app.api.error_handlers import ApiError
from app.services.vehicle_cropping import crop_vehicle
from app.services.plate_consensus import PlateCandidate, consensus
from app.services.inference_metrics import InferenceMetrics

class EnrichmentWorker:
    def __init__(self, jobs, service, processor, logger):
        self.jobs,self.service,self.processor,self.logger=jobs,service,processor,logger
        self.stop_event=threading.Event()
        self.thread=threading.Thread(target=self._run,daemon=True,name="enrichment-worker")

    def start(self):
        self.thread.start()

    def close(self):
        self.stop_event.set()
        self.thread.join(timeout=2)

    def _run(self):
        while not self.stop_event.is_set():
            job=self.jobs.dequeue()
            if job is None:
                self.stop_event.wait(.1)
                continue
            try:
                self._process(job)
            except Exception:
                if not self.stop_event.is_set():
                    self.logger.error("enrichment_job_failed",extra={"job_id":job.enrichment_job_id,"error_code":"processing_failed"})
                    self.jobs.fail(job.enrichment_job_id,"processing_failed")

    def _continue(self,job):
        return not self.stop_event.is_set() and self.jobs.is_processing(job.enrichment_job_id)

    def _interrupted_status(self,job):
        if self.stop_event.is_set():
            return "cancelled"
        try:
            return self.jobs.get(job.enrichment_job_id,job.owner_key_id).status.value
        except ApiError:
            return "expired"

    def _process(self,job):
        with InferenceMetrics(self.logger,"enrichment_job",request_id=job.source_id,
                              job_id=job.enrichment_job_id,source_type=job.source_kind) as metrics:
            if not self._continue(job):
                metrics.status=self._interrupted_status(job)
                return
            source=self.service.resolve(job.source_kind,job.source_id,job.owner_key_id)
            units=self.service.units_for_source(job.source_kind,source,job.owner_key_id)
            image=None
            if job.source_kind=="image":
                data,_=self.service.images.read_original(job.source_id,job.owner_key_id)
                image=cv2.imdecode(np.frombuffer(data,dtype=np.uint8),cv2.IMREAD_COLOR)
            capture=cv2.VideoCapture(str(source.staged_path)) if job.source_kind=="video" else None
            results=[]
            try:
                for position,unit in enumerate(units,start=1):
                    if not self._continue(job):
                        metrics.status=self._interrupted_status(job)
                        return
                    evidence=unit.get("evidence",[unit["bbox"]])
                    outputs=[]
                    with InferenceMetrics(self.logger,"enrichment_unit",request_id=job.source_id,
                                          job_id=job.enrichment_job_id,source_type=job.source_kind) as unit_metrics:
                        for detection in evidence:
                            if not self._continue(job):
                                unit_metrics.status=metrics.status=self._interrupted_status(job)
                                return
                            frame=image
                            if capture is not None:
                                capture.set(cv2.CAP_PROP_POS_FRAMES,detection.frame_index)
                                ok,frame=capture.read()
                                if not ok:
                                    continue
                            crop=crop_vehicle(frame,detection,self.service.settings.vehicle_class_set())
                            if crop is not None:
                                index=detection.frame_index if capture is not None else None
                                attrs,plate=self.processor.enrich(crop.image,index,request_id=job.source_id,
                                    job_id=job.enrichment_job_id,source_type=job.source_kind,should_continue=lambda:self._continue(job))
                                outputs.append((index,attrs,plate))
                            if not self._continue(job):
                                unit_metrics.status=metrics.status=self._interrupted_status(job)
                                return
                    if not self._continue(job):
                        metrics.status=self._interrupted_status(job)
                        return
                    attributes={"status":"failed","items":[],"error_code":"crop_unavailable"}
                    plate={"status":"failed","used_enhancement":False,"evidence_frame_indexes":[],"error_code":"crop_unavailable"}
                    if outputs:
                        _,attributes,plate=outputs[0]
                    if unit["track_id"] is not None:
                        candidates=[PlateCandidate(value.get("text",""),value.get("ocr_confidence") or 0,
                            value.get("localizer_confidence") or 0,1.0,index)
                            for index,_,value in outputs if value.get("status")=="read"]
                        winner=consensus(candidates,self.processor.accept_threshold)
                        if winner is None and candidates:
                            plate={**plate,"status":"unreadable","text":None}
                        elif winner is not None:
                            # Keep geometry from the same observed frame as the selected reading.
                            observed=next((v for index,_,v in outputs if index==winner.frame_index),plate)
                            plate={**observed,"status":"read","text":winner.text,"ocr_confidence":winner.ocr_confidence,
                                   "evidence_frame_indexes":[c.frame_index for c in candidates if c.text==winner.text and c.frame_index is not None]}
                    if job.source_kind=="image" and "provenance" not in plate:
                        from app.services.plate_reading_policy import provenance
                        plate={**plate,"provenance":provenance(getattr(getattr(self.processor,"image_policy",None),"policy_id","baseline-v1"),[])}
                    results.append({"vehicle_key":f"track-{unit['track_id']}" if unit["track_id"] else f"detection-{unit['detection_id']}",
                        "detection_id":unit["detection_id"],"track_id":unit["track_id"],"class_id":unit["class_id"],
                        "class_name":unit["class_name"],"evidence_frame_indexes":[d.frame_index for d in evidence] if unit["track_id"] else [],
                        "attributes_status":attributes["status"],"plate_status":plate["status"],"attributes":attributes["items"],
                        "plate":plate,"error_code":attributes.get("error_code") or plate.get("error_code")})
                    self.jobs.progress(job.enrichment_job_id,position)
            finally:
                if capture is not None:
                    capture.release()
            if self._continue(job):
                metrics.status=self.jobs.finish(job.enrichment_job_id,results)
            else:
                metrics.status=self._interrupted_status(job)
