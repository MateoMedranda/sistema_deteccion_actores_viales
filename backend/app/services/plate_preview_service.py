"""Authorized plate evidence orchestration. HTTP routes do not touch files/models."""
import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass,field
from threading import BoundedSemaphore,Event
from time import monotonic
from datetime import UTC,datetime
import cv2
import numpy as np
from app.api.error_handlers import ApiError
from app.domain.schemas import PlatePreviewMetadata
from app.services.plate_geometry import plate_roi
from app.services.plate_profiles import display_contrast,NotApplicable
from app.services.plate_preview_store import PreviewValue
from app.services.inference_metrics import InferenceMetrics
@dataclass
class PreviewRequest:
    deadline:float
    disconnected:object
    closed:Event
    retired:Event=field(default_factory=Event)
    def guard(self):
        if self.retired.is_set() or self.closed.is_set():raise ApiError(503,"plate_preview_unavailable","Preview was abandoned.")
        if monotonic()>=self.deadline:raise ApiError(504,"plate_preview_timeout","Preview timed out.")
    async def check(self):
        self.guard()
        if await self.disconnected():raise ApiError(503,"plate_preview_unavailable","Preview was abandoned.")

class PlatePreviewService:
    def __init__(self,jobs,images,store):
        self.jobs,self.images,self.store=jobs,images,store
        self.logger=logging.getLogger("road_actor_detection")
        self.request_timeout=8.0
        self._closed=Event()
        self._access_slots=BoundedSemaphore(4)
        self._access_pool=ThreadPoolExecutor(max_workers=4,thread_name_prefix="plate-preview-access")

    async def _access(self,operation,request,discard=None):
        """No blocking lock or I/O on ASGI; no queued access workers."""
        request.guard()
        if not self._access_slots.acquire(blocking=False):raise ApiError(429,"plate_preview_busy","Preview is busy.")
        retired=Event()
        completed=asyncio.Event()
        loop=asyncio.get_running_loop()
        def execute():
            request.guard()
            return operation()
        try:future=self._access_pool.submit(execute)
        except BaseException:
            self._access_slots.release()
            raise ApiError(503,"plate_preview_unavailable","Preview is unavailable.") from None
        def discard_result():
            if discard:
                try:discard(future.result())
                except BaseException:pass
        def finished(_):
            self._access_slots.release()
            if retired.is_set():discard_result()
            try:loop.call_soon_threadsafe(completed.set)
            except RuntimeError:pass  # The requester may already have closed its loop.
        future.add_done_callback(finished)
        delivered=False
        try:
            while not future.done():
                await request.check()
                try:await asyncio.wait_for(completed.wait(),timeout=min(.05,max(0,request.deadline-monotonic())))
                except asyncio.TimeoutError:pass
            await request.check()
            value=future.result()
            delivered=True
            return value
        except ApiError:raise
        except asyncio.CancelledError:raise
        except Exception:raise ApiError(503,"plate_preview_unavailable","Preview is unavailable.") from None
        finally:
            if not delivered:
                retired.set()
                if future.done():discard_result()

    def close(self):
        self._closed.set()
        self._access_pool.shutdown(wait=False,cancel_futures=True)
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
        request=PreviewRequest(monotonic()+self.request_timeout,disconnected,self._closed)
        try:return await self._get(job_id,detection_id,owner,request_id,request)
        finally:request.retired.set()

    async def _get(self,job_id,detection_id,owner,request_id,request):
        source,job,roi=await self._access(lambda:self.resolve(job_id,detection_id,owner),request)
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
                check()
                metadata=PlatePreviewMetadata(version=1,source_id=source.source_id,enrichment_job_id=job_id,detection_id=detection_id,profile_id="display-contrast-v1",
                    input_size={"width":x2-x1,"height":y2-y1},output_size={"width":size[0],"height":size[1]},
                    original_bbox=dict(zip(("x_min","y_min","x_max","y_max"),roi)),applied_steps=steps,
                    original_to_processed=[scale,0,0,0,scale,0],expires_at=expires)
                header=json.dumps(metadata.model_dump(mode="json"),ensure_ascii=True,separators=(",",":"))
                check()
                return PreviewValue(png,header,expires)
            except NotApplicable:
                raise ApiError(422,"plate_not_applicable","This plate cannot use the visual profile.") from None
            except ApiError as exc:
                raise
            except Exception:
                raise ApiError(503,"plate_preview_unavailable","Preview is unavailable.") from None
        consumer=await self._access(lambda:self.store.acquire(key,expires,compute,validate,measure=lambda:InferenceMetrics(self.logger,"plate_preview",request_id=request_id,job_id=job_id,source_type="image",profile_id="display-contrast-v1",defer_emit=True),before_admit=request.guard),request,discard=self.store.release)
        try:
            while not consumer.future.done():
                await request.check()
                if expires<=datetime.now(UTC):raise ApiError(410,"source_expired","Evidence expired.")
                if consumer.flight and self.store.timer()>=consumer.flight.deadline:raise ApiError(504,"plate_preview_timeout","Preview timed out.")
                await asyncio.sleep(.02)
            try:value=consumer.future.result()
            except ApiError:raise
            except Exception:raise ApiError(503,"plate_preview_unavailable","Preview is unavailable.") from None
            await request.check()
            await self._access(validate,request)
            if value.expires_at<=datetime.now(UTC):raise ApiError(410,"source_expired","Evidence expired.")
            return value
        finally:self.store.release(consumer)
