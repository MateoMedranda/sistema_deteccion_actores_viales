from __future__ import annotations
import concurrent.futures
import threading
import logging
from dataclasses import asdict
import numpy as np
from app.services.plate_quality import conservative_enhance, rectify_plate
from app.services.image_geometry import clip_box
from app.services.inference_metrics import InferenceMetrics
from app.services.plate_reading_policy import BaselinePolicy,provenance

class EnrichmentProcessor:
    def __init__(self, attributes, localizer, reader, retry_threshold, accept_threshold, max_attribute=1, max_plate=1):
        self.attributes, self.localizer, self.reader = attributes, localizer, reader
        self.retry_threshold, self.accept_threshold = retry_threshold, accept_threshold
        self.attribute_slots = threading.BoundedSemaphore(max_attribute)
        self.plate_slots = threading.BoundedSemaphore(max_plate)
        self.logger = logging.getLogger("road_actor_detection")
        self.image_policy=BaselinePolicy()

    @property
    def capabilities(self):
        return {"attributes": "ready" if self.attributes is not None else "unavailable",
                "plate_localization": "ready" if self.localizer is not None else "unavailable",
                "plate_ocr": "ready" if self.reader is not None else "unavailable"}

    @property
    def usable(self):
        return self.attributes is not None or self.localizer is not None

    def enrich(self, crop: np.ndarray, frame_index=None, *, request_id=None, job_id=None, source_type="image", should_continue=None):
        context = {"request_id": request_id, "job_id": job_id, "source_type": source_type}
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            attrs = executor.submit(self._attributes, crop, frame_index, context)
            plate = executor.submit(self._plate, crop, frame_index, context, should_continue)
            return attrs.result(), plate.result()

    def _attributes(self, crop, frame_index, context=None):
        with InferenceMetrics(self.logger, "attributes", **(context or {})) as metric:
            if self.attributes is None:
                metric.fail("attribute_model_unavailable")
                return {"status":"failed","items":[],"error_code":"attribute_model_unavailable"}
            try:
                with self.attribute_slots:
                    output = self.attributes.extract(crop)
                return {"status":"completed","items":[{**asdict(item),"evidence_frame_index":frame_index} for item in output]}
            except Exception:
                metric.fail("attribute_processing_failed")
                return {"status":"failed","items":[],"error_code":"attribute_processing_failed"}

    def _plate(self, crop, frame_index, context=None, should_continue=None):
        context = context or {}
        with InferenceMetrics(self.logger, "plate", **context) as metric:
            result = self._plate_impl(crop, frame_index, context, should_continue)
            if context.get("source_type","image")=="image" and "provenance" not in result:
                result["provenance"]=provenance(self.image_policy.policy_id,[])
            if result["status"] == "failed":
                metric.fail(result.get("error_code","plate_processing_failed"))
            return result

    def _plate_impl(self, crop, frame_index, context, should_continue=None):
        empty = {"used_enhancement":False,"evidence_frame_indexes":[] if frame_index is None else [frame_index]}
        if self.localizer is None:
            return {"status":"failed",**empty,"error_code":"plate_model_unavailable"}
        stage, evidence = "localization", {}
        try:
            with InferenceMetrics(self.logger, "plate_localization", **context):
                with self.plate_slots:
                    location = self.localizer.locate(crop)
            if location is None:
                return {"status":"not_detected",**empty}
            height, width = crop.shape[:2]
            box = clip_box(location.x_min,location.y_min,location.x_max,location.y_max,width,height)
            if box is None:
                return {"status":"unreadable",**empty}
            x1,y1,x2,y2 = box
            evidence = {"bbox_relative":{"x_min":x1/width,"y_min":y1/height,"x_max":x2/width,"y_max":y2/height},
                        "localizer_confidence":location.confidence}
            if self.reader is None:
                return {"status":"failed",**empty,**evidence,"error_code":"plate_reader_unavailable"}
            stage = "ocr"
            plate = crop[y1:y2,x1:x2].copy()
            if context.get("source_type","image")=="image":
                def read(candidate):
                    with self.plate_slots:
                        if should_continue is not None and not should_continue():raise RuntimeError("cancelled")
                        return self.reader.read(candidate)
                with InferenceMetrics(self.logger,"plate_ocr",**context) as ocr_metric:
                    output=self.image_policy.read(plate,read,self.retry_threshold,self.accept_threshold,should_continue or (lambda:True))
                    if output["status"]=="failed":ocr_metric.fail("plate_processing_failed")
                if output["status"]=="failed":
                    self.logger.error("plate_processing_failed",extra={"branch":"ocr","exception_type":output.pop("_exception_type","RuntimeError"),"error_code":"plate_processing_failed"})
                return {**empty,**evidence,**output}
            with InferenceMetrics(self.logger, "plate_ocr", **context):
                with self.plate_slots:
                    reading = self.reader.read(plate)
                enhanced = False
                if reading is None or reading.confidence < self.retry_threshold:
                    enhanced = True
                    with self.plate_slots:
                        retried = self.reader.read(conservative_enhance(rectify_plate(plate)))
                    if retried is not None and (reading is None or retried.confidence > reading.confidence):
                        reading = retried
            result = {"status":"unreadable",**empty,**evidence,"ocr_confidence":reading.confidence if reading else None,
                      "used_enhancement":enhanced}
            if reading is not None and reading.confidence >= self.accept_threshold and reading.text:
                result.update(status="read",text=reading.text)
            return result
        except Exception as exc:
            self.logger.error("plate_processing_failed",extra={"branch":stage,"exception_type":type(exc).__name__,
                              "error_code":"plate_processing_failed"})
            return {"status":"failed",**empty,**evidence,"error_code":"plate_processing_failed"}
