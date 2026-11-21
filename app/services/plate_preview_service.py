"""Authorized plate evidence orchestration. HTTP routes do not touch files/models."""
import asyncio
import json
import logging
from datetime import UTC,datetime
import cv2
import numpy as np
from app.api.error_handlers import ApiError
from app.domain.schemas import PlatePreviewMetadata
from app.services.plate_geometry import plate_roi
from app.services.plate_profiles import display_contrast,NotApplicable
from app.services.plate_preview_store import PreviewValue
from app.services.inference_metrics import InferenceMetrics
class PlatePreviewService:
    def __init__(self,jobs,images,store):
        self.jobs,self.images,self.store=jobs,images,store
        self.logger=logging.getLogger("road_actor_detection")
    def resolve(self,job_id,detection_id,owner):
        job=self.jobs.get(job_id,owner)
        if job.status.value!="completed" or job.source_kind!="image":raise ApiError(409,"preview_source_not_ready","Image results are not ready.")
        source=self.images.get(job.source_id,owner)
        item=self.jobs.result_by_detection(job_id,owner,detection_id)
        if not 1<=detection_id<=len(source.detections):raise ApiError(404,"detection_not_found","No accessible detection was found.")
        detection=source.detections[detection_id-1]
        if item.track_id is not None or item.class_id!=detection.class_id or item.class_name!=detection.class_name or item.vehicle_key!=f"detection-{detection_id}":
            raise ApiError(422,"plate_not_applicable","Plate evidence is not applicable.")
        if item.plate.status=="not_detected" or item.plate.bbox_relative is None:raise ApiError(422,"plate_not_applicable","No localized plate is available.")
        try:roi=plate_roi(detection,item.plate.bbox_relative,source.width,source.height)
        except ValueError:raise ApiError(422,"plate_not_applicable","Plate evidence is not applicable.") from None
        return source,job,roi
    async def get(self,job_id,detection_id,owner,request_id,disconnected):
        source,job,roi=self.resolve(job_id,detection_id,owner)
        expires=min(source.expires_at,job.expires_at)
        key=(owner,source.source_id,job_id,detection_id,"display-contrast-v1")
        def validate():
            current,current_job,current_roi=self.resolve(job_id,detection_id,owner)
            if current_roi!=roi or min(current.expires_at,current_job.expires_at)!=expires:raise ApiError(410,"source_expired","Evidence changed or expired.")
        def compute(check):
            try:
                check();validate()
                data,actual=self.images.read_original(source.source_id,owner)
                check()
                image=cv2.imdecode(np.frombuffer(data,np.uint8),cv2.IMREAD_COLOR)
                if image is None or image.shape[:2]!=(actual.height,actual.width):raise RuntimeError("invalid_original")
                x1,y1,x2,y2=roi
                crop=image[y1:y2,x1:x2].copy();del image,data
                check();png,size,scale,steps=display_contrast(crop);del crop
                check();validate()
                metadata=PlatePreviewMetadata(version=1,source_id=source.source_id,enrichment_job_id=job_id,detection_id=detection_id,profile_id="display-contrast-v1",
                    input_size={"width":x2-x1,"height":y2-y1},output_size={"width":size[0],"height":size[1]},
                    original_bbox=dict(zip(("x_min","y_min","x_max","y_max"),roi)),applied_steps=steps,
                    original_to_processed=[scale,0,0,0,scale,0],expires_at=expires)
                header=json.dumps(metadata.model_dump(mode="json"),ensure_ascii=True,separators=(",",":"))
                check();validate()
                return PreviewValue(png,header,expires)
            except NotApplicable:
                raise ApiError(422,"plate_not_applicable","This plate cannot use the visual profile.") from None
            except ApiError as exc:
                raise
            except Exception:
                raise ApiError(503,"plate_preview_unavailable","Preview is unavailable.") from None
        consumer=self.store.acquire(key,expires,compute,validate,measure=lambda:InferenceMetrics(self.logger,"plate_preview",request_id=request_id,job_id=job_id,source_type="image",profile_id="display-contrast-v1"))
        try:
            while not consumer.future.done():
                if await disconnected():raise ApiError(503,"plate_preview_unavailable","Preview was abandoned.")
                if consumer.flight:self.store.check(consumer.flight)
                validate()
                await asyncio.sleep(.02)
            try:value=consumer.future.result()
            except ApiError:raise
            except Exception:raise ApiError(503,"plate_preview_unavailable","Preview is unavailable.") from None
            validate()
            if value.expires_at<=datetime.now(UTC):raise ApiError(410,"source_expired","Evidence expired.")
            return value
        finally:self.store.release(consumer)
