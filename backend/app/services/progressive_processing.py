"""Progressive analysis only. Annotated video export is an explicit separate job."""

from time import perf_counter
import psutil
from app.adapters.timed_video_decoder import TimedVideoDecoder
from app.services.video_presentation import PresentationFilter
from app.services.video_profile import VideoProfile


class ProgressiveProcessor:
    def __init__(self, processor, store, evidence=None):
        self.processor, self.store, self.evidence = processor, store, evidence

    def process(self, job):
        from app.services.video_processing import IoUTracker, VideoProcessingError

        p = self.processor
        store = self.store
        started = perf_counter()
        metrics = dict(decode_ms=0, inference_ms=0, evidence_ms=0, render_ms=0, publish_ms=0)
        profile = VideoProfile(job, p.detector, p.profile_root)
        profile.sampling["requested_interval"] = getattr(p, "detection_interval", 1)
        p.progressive_metrics = metrics
        batch = []
        prepared = []
        count = 0
        tracker = IoUTracker()
        model = None
        frames = None
        display = PresentationFilter()
        decoder = TimedVideoDecoder(job.staged_path)

        def check():
            with profile.measure("controls"):
                store.row(job.job_id)
                if p.store.is_cancelled(job.job_id):
                    raise VideoProcessingError("job_cancelled")
                if perf_counter() - started >= p.timeout_seconds:
                    raise VideoProcessingError("job_timeout")

        def publish():
            if not batch:
                return
            check()
            before = perf_counter()
            with profile.measure("publication"):
                store.publish(
                    job.job_id,
                    batch,
                    on_publish=(lambda: self.evidence.commit(job, prepared, batch))
                    if self.evidence
                    else None,
                )
                metrics["publish_ms"] += (perf_counter() - before) * 1000
                p.store.progress(job.job_id, count)
            profile.confirmed(count, batch[-1]["end_us"], store.buffer_seconds)
            batch.clear()
            prepared.clear()

        try:
            with profile.measure("setup"):
                model = p.detector.create_video_tracker() if hasattr(p.detector, "create_video_tracker") else None
                if model is not None and hasattr(model, "set_detection_interval"):
                    model.set_detection_interval(profile.sampling["requested_interval"])
                    profile.sampling["effective_interval"] = model.detection_interval
                elif profile.sampling["requested_interval"] != 1:
                    p.logger.warning("video_detection_interval_fallback", extra={"job_id": job.job_id})
                frames = iter(decoder)
            while True:
                before_decode = perf_counter()
                with profile.measure("decode"):
                    try:
                        frame = next(frames)
                    except StopIteration:
                        break
                metrics["decode_ms"] += (perf_counter() - before_decode) * 1000
                frame_started = perf_counter()
                check()
                image = frame.image
                with profile.measure("setup"):
                    if count == 0:
                        store.set_timeline(job.job_id, decoder.timeline)
                        h, w = image.shape[:2]
                        with p.store._lock, p.store._connection:
                            p.store._connection.execute(
                                "UPDATE video_jobs SET width=?,height=? WHERE job_id=?",
                                (w, h, job.job_id),
                            )
                before = perf_counter()
                requires_detection = model is None or getattr(model, "requires_detection", True)
                if requires_detection:
                    with profile.measure("resource_wait"):
                        p.progressive_inference_slots.acquire()
                try:
                    if model is not None:
                        try:
                            if hasattr(model, "track_profiled"):
                                pairs = model.track_profiled(image, profile)
                            else:
                                with profile.measure("detection_tracking_combined"):
                                    pairs = model.track(image)
                        except ModuleNotFoundError as e:
                            if e.name != "scipy":
                                raise
                            model = None
                            profile.sampling["effective_interval"] = 1
                            p.logger.warning("video_detection_interval_fallback", extra={"job_id": job.job_id})
                    if model is None:
                        with profile.measure("detection"):
                            detections = p.detector.detect(image)
                        with profile.measure("tracking"):
                            pairs = list(zip(detections, tracker.assign(detections), strict=True))
                finally:
                    if requires_detection:
                        p.progressive_inference_slots.release()
                detection_performed = model is None or getattr(model, "last_was_detection", True)
                metrics["inference_ms"] += (perf_counter() - before) * 1000
                before = perf_counter()
                with profile.measure("presentation"):
                    observed = [
                        dict(
                            track_id=tid,
                            class_name=d.class_name,
                            bbox=(d.x_min, d.y_min, d.x_max, d.y_max),
                        )
                        for d, tid in pairs
                    ]
                    boxes = display.present(image, frame.frame_index, observed)
                    observations = []
                    for d, tid in pairs:
                        bbox = {k: getattr(d, k) for k in ("x_min", "y_min", "x_max", "y_max")}
                        box = boxes.get(tid)
                        observations.append(
                            dict(
                                track_id=tid,
                                class_id=d.class_id,
                                class_name=d.class_name,
                                confidence=d.confidence,
                                raw_bbox=bbox,
                                display_bbox=dict(
                                    zip(("x_min", "y_min", "x_max", "y_max"), map(int, box))
                                )
                                if box
                                else None,
                            )
                        )
                metrics["render_ms"] += (perf_counter() - before) * 1000
                before = perf_counter()
                with profile.measure("evidence"):
                    if self.evidence and detection_performed:
                        prepared.extend(self.evidence.prepare(job, frame, pairs))
                metrics["evidence_ms"] += (perf_counter() - before) * 1000
                before = perf_counter()
                count += 1
                profile.frames = count
                profile.sampling["detected_frames" if detection_performed else "predicted_frames"] += 1
                metrics["render_ms"] += (perf_counter() - before) * 1000
                batch.append(
                    dict(
                        frame_index=frame.frame_index,
                        start_us=frame.start_us,
                        end_us=frame.end_us,
                        pts=str(frame.pts),
                        detection_performed=detection_performed,
                        observations=observations,
                    )
                )
                if (
                    len(batch) >= p.progressive_batch_frames
                    or batch[-1]["end_us"] - batch[0]["start_us"] >= p.progressive_batch_us
                ):
                    publish()
                with profile.measure("frame_logging"):
                    p.logger.info("video_frame_processed", extra={"job_id":job.job_id,"source_type":"video","progress":count,"frame_ms":round((perf_counter()-frame_started)*1000,3),"memory_mb":round(psutil.Process().memory_info().rss/1024**2,2),"tracker":"model" if model is not None else "iou-fallback"})
                profile.checkpoint(p.logger)
            publish()
            if count == 0:
                raise VideoProcessingError("invalid_video")
            metrics["analysis_ms"] = (perf_counter() - started) * 1000
            profile.end_analysis(complete=True)
            with profile.measure("finalization"):
                store.finish_analysis(job.job_id)
            with profile.measure("finalization"):
                with p.store._lock, p.store._connection:
                    row = p.store.get(job.job_id, job.owner_key_id)
                    if p.store.is_cancelled(job.job_id):
                        raise VideoProcessingError("job_cancelled")
                    classes = [
                        r[0]
                        for r in p.store._connection.execute(
                            "SELECT DISTINCT class_name FROM video_detections WHERE job_id=?",
                            (job.job_id,),
                        )
                    ]
                    eligible = (
                        p.store._connection.execute(
                            "SELECT COUNT(DISTINCT track_id) FROM video_detections WHERE job_id=? AND lower(class_name) IN ("
                            + ",".join("?" * len(p.eligible_classes))
                            + ")",
                            (job.job_id, *p.eligible_classes),
                        ).fetchone()[0]
                        if p.eligible_classes
                        else 0
                    )
                    p.store._connection.execute(
                        "UPDATE video_jobs SET status='completed',processing_phase='ready',output_path=NULL,actual_frame_count=?,total_frames=?,processed_frames=?,frame_total_confirmed=1,eligible_track_count=?,classes_present=? WHERE job_id=?",
                        (
                            count,
                            count,
                            count,
                            eligible,
                            __import__("json").dumps(sorted(classes)),
                            job.job_id,
                        ),
                    )
            profile.outcome = "completed"
            return "completed"
        except Exception as exc:
            profile.end_analysis()
            code = (
                str(exc)
                if str(exc)
                in (
                    "job_timeout",
                    "job_cancelled",
                    "video_encoding_failed",
                    "timeline_unrepresentable",
                )
                else "processing_failed"
            )
            profile.outcome = "cancelled" if code == "job_cancelled" else "failed"
            profile.error_code = code
            diagnostic=str(exc) if isinstance(exc,ValueError) and str(exc) in ("invalid_observation","non_contiguous_batch","conflicting_batch","timeline_unrepresentable") else code
            p.logger.error("progressive_processing_failed",extra={"job_id":job.job_id,"error_code":diagnostic,"exception_type":type(exc).__name__,"progress":count,"source_type":"video"})
            try:
                row = store.row(job.job_id)
                if row["analysis"] != "complete":
                    store.finish_analysis(job.job_id, code)
                store.export(job.job_id, "failed")
            except Exception:
                pass
            if isinstance(exc, VideoProcessingError):
                raise
            raise VideoProcessingError(code) from exc
        finally:
            with profile.measure("cleanup"):
                if frames is not None:
                    frames.close()
                p.store.release(job.job_id)
                if self.evidence:
                    self.evidence.discard_pending(job.job_id)
            profile.end_analysis()
            if profile.save(p.logger):
                p.logger.info("video_profile_ready", extra={"job_id": job.job_id, "status": profile.outcome})
            p.logger.info(
                "progressive_video_outcome",
                extra={
                    "job_id": job.job_id,
                    "progress": count,
                    "elapsed_ms": round((perf_counter() - started) * 1000),
                    "inference_ms": round(metrics["inference_ms"]),
                    "output_ms": round(metrics["publish_ms"]),
                    "memory_mb":round(psutil.Process().memory_info().rss/1024**2,2),
                },
            )
