from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path
from time import perf_counter

import cv2
import numpy as np
import psutil

from app.adapters.detector_protocol import Detector
from app.domain.models import Detection, FrameDetection, VideoJob
from app.services.video_artifacts import VideoArtifactStore
from app.services.video_job_store import VideoJobStore


class VideoProcessingError(RuntimeError):
    """Expected, safe failures while processing an accepted video job."""


class IoUTracker:
    """Small per-job tracker used until a separately evaluated ByteTrack adapter is introduced."""

    def __init__(self) -> None:
        self._next_id = 1
        self._previous: list[tuple[int, Detection]] = []

    def assign(self, detections: list[Detection]) -> list[int]:
        assigned: list[int] = []
        used: set[int] = set()
        for detection in detections:
            match = next(
                (
                    track_id for track_id, previous in self._previous
                    if track_id not in used and previous.class_id == detection.class_id
                    and self._iou(previous, detection) >= 0.3
                ),
                None,
            )
            if match is None:
                match = self._next_id
                self._next_id += 1
            used.add(match)
            assigned.append(match)
        self._previous = list(zip(assigned, detections, strict=True))
        return assigned

    @staticmethod
    def _iou(left: Detection, right: Detection) -> float:
        x1, y1 = max(left.x_min, right.x_min), max(left.y_min, right.y_min)
        x2, y2 = min(left.x_max, right.x_max), min(left.y_max, right.y_max)
        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        if not intersection:
            return 0.0
        left_area = (left.x_max - left.x_min) * (left.y_max - left.y_min)
        right_area = (right.x_max - right.x_min) * (right.y_max - right.y_min)
        return intersection / max(1, left_area + right_area - intersection)


class VideoProcessor:
    def __init__(self,detector,store,artifacts,ffmpeg_executable,timeout_seconds,logger,eligible_classes=()):
        self.detector,self.store,self.artifacts=detector,store,artifacts
        self.ffmpeg_executable,self.timeout_seconds,self.logger=ffmpeg_executable,timeout_seconds,logger
        self.eligible_classes=set(eligible_classes);self.encoder_peak_rss=0

    def process(self,job):
        progressive=getattr(self,"progressive",None)
        if progressive is not None and progressive.exists(job.job_id):
            from app.services.progressive_processing import ProgressiveProcessor
            return ProgressiveProcessor(self,progressive,getattr(self,'evidence',None)).process(job)
        from app.services.video_presentation import PresentationFilter,draw_box
        import os
        if job.staged_path is None:raise VideoProcessingError("missing_input")
        capture=cv2.VideoCapture(os.path.relpath(job.staged_path))
        if not capture.isOpened():raise VideoProcessingError("invalid_video")
        temporary=self.artifacts.annotated_output_path().with_suffix(".raw.mp4")
        output=self.artifacts.annotated_output_path()
        self.store.register_path(job.job_id,temporary);self.store.register_path(job.job_id,output)
        writer=cv2.VideoWriter(os.path.relpath(temporary),cv2.VideoWriter_fourcc(*"mp4v"),job.metadata.fps,(job.metadata.width,job.metadata.height))
        started=perf_counter();outcome="failed";frame_index=0;detections=[];self.encoder_peak_rss=0
        display=PresentationFilter();tracker=IoUTracker()
        model_tracker=self.detector.create_video_tracker() if hasattr(self.detector,"create_video_tracker") else None
        def cancelled():return self.store.is_cancelled(job.job_id)
        def stop_check():
            if cancelled():raise VideoProcessingError("job_cancelled")
            if perf_counter()-started>=self.timeout_seconds:raise VideoProcessingError("job_timeout")
        try:
            if not writer.isOpened():raise VideoProcessingError("output_initialization_failed")
            while True:
                stop_check();ok,frame=capture.read()
                if not ok:break
                if frame.shape[:2]!=(job.metadata.height,job.metadata.width):raise VideoProcessingError("video_geometry_invalid")
                frame_started=perf_counter()
                if model_tracker is not None:
                    try:pairs=model_tracker.track(frame)
                    except ModuleNotFoundError as exc:
                        if exc.name!="scipy":raise
                        model_tracker=None
                        self.logger.warning("video_tracker_fallback",extra={"job_id":job.job_id,"error_code":"bytetrack_dependency_unavailable"})
                if model_tracker is None:
                    raw=self.detector.detect(frame);pairs=list(zip(raw,tracker.assign(raw),strict=True))
                observations=[{"track_id":tid,"class_name":d.class_name,"bbox":(d.x_min,d.y_min,d.x_max,d.y_max)} for d,tid in pairs]
                boxes=display.present(frame,frame_index,observations)
                for detection,track_id in pairs:
                    if track_id in boxes:draw_box(frame,boxes[track_id],detection.class_name)
                    detections.append(FrameDetection(frame_index,track_id,detection.class_id,detection.class_name,detection.confidence,detection.x_min,detection.y_min,detection.x_max,detection.y_max))
                writer.write(frame);frame_index+=1;self.store.progress(job.job_id,frame_index)
                self.logger.info("video_frame_processed",extra={"job_id":job.job_id,"progress":frame_index,"frame_ms":round((perf_counter()-frame_started)*1000),"memory_mb":round(psutil.Process().memory_info().rss/1024**2,2),"tracker":"model" if model_tracker is not None else "iou-fallback"})
            capture.release();writer.release()
            stop_check()
            if frame_index<=0:raise VideoProcessingError("invalid_video")
            self.store.phase(job.job_id,"encoding",frame_index)
            self._encode_h264(temporary,output,cancelled,started+self.timeout_seconds,job.expires_at)
            stop_check();self.store.phase(job.job_id,"publishing")
            outcome=self.store.finish(job.job_id,output,detections,actual_frame_count=frame_index,eligible_classes=self.eligible_classes,owner_key_id=job.owner_key_id)
            return outcome
        finally:
            capture.release();writer.release();temporary.unlink(missing_ok=True)
            if outcome!="completed":output.unlink(missing_ok=True)
            if outcome!="completed":
                try:outcome=self.store.get(job.job_id,job.owner_key_id).status.value
                except Exception:outcome="expired"
                if outcome=="processing":outcome="failed"
            self.store.release(job.job_id)
            self.logger.info("video_job_outcome",extra={"job_id":job.job_id,"outcome":outcome,"elapsed_ms":round((perf_counter()-started)*1000),"progress":frame_index,"memory_mb":round((psutil.Process().memory_info().rss+self.encoder_peak_rss)/1024**2,2)})
    def _encode_h264(self,source,destination,cancelled=lambda:False,deadline=None,expires_at=None):
        import time
        from datetime import UTC,datetime
        process=None
        end=min(perf_counter()+60,deadline or float("inf"))
        try:
            process=subprocess.Popen([self.ffmpeg_executable,"-nostdin","-y","-i",str(source),"-c:v","libx264","-movflags","+faststart",str(destination)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            while process.poll() is None:
                if cancelled() or (expires_at and datetime.now(UTC)>=expires_at):raise VideoProcessingError("job_cancelled")
                if perf_counter()>=end:raise VideoProcessingError("video_encoding_failed")
                try:self.encoder_peak_rss=max(self.encoder_peak_rss,psutil.Process(process.pid).memory_info().rss)
                except psutil.Error:pass
                time.sleep(.05)
            if process.returncode!=0:raise VideoProcessingError("video_encoding_failed")
        except (OSError,subprocess.SubprocessError) as exc:
            raise VideoProcessingError("video_encoding_failed") from exc
        finally:
            if process is not None and process.poll() is None:
                process.terminate()
                try:process.wait(timeout=1)
                except subprocess.TimeoutExpired:process.kill();process.wait()
            if process is None or process.returncode!=0 or cancelled():destination.unlink(missing_ok=True)

    @staticmethod
    def _annotate(frame,detection,track_id):
        from app.services.video_presentation import draw_box
        draw_box(frame,(detection.x_min,detection.y_min,detection.x_max,detection.y_max),detection.class_name)
