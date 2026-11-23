"""Single inference pass for progressive source-time playback and legacy CFR export."""

from time import perf_counter
import os
import cv2
from app.adapters.timed_video_decoder import TimedVideoDecoder
from app.services.video_presentation import PresentationFilter, draw_box


class ProgressiveProcessor:
    def __init__(self, processor, store, evidence=None):
        self.processor, self.store, self.evidence = processor, store, evidence

    def process(self, job):
        from app.services.video_processing import IoUTracker, VideoProcessingError

        p = self.processor
        store = self.store
        raw = p.artifacts.annotated_output_path().with_suffix(".raw.mp4")
        output = p.artifacts.annotated_output_path()
        p.store.register_path(job.job_id, raw)
        p.store.register_path(job.job_id, output)
        started = perf_counter()
        metrics = dict(decode_ms=0, inference_ms=0, evidence_ms=0, render_ms=0, publish_ms=0)
        previous = started
        p.progressive_metrics = metrics
        writer = None
        batch = []
        prepared = []
        count = 0
        tracker = IoUTracker()
        model = (
            p.detector.create_video_tracker()
            if hasattr(p.detector, "create_video_tracker")
            else None
        )
        display = PresentationFilter()
        decoder = TimedVideoDecoder(job.staged_path)

        def check():
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
            store.publish(
                job.job_id,
                batch,
                on_publish=(lambda: self.evidence.commit(job, prepared, batch))
                if self.evidence
                else None,
            )
            metrics["publish_ms"] += (perf_counter() - before) * 1000
            p.store.progress(job.job_id, count)
            batch.clear()
            prepared.clear()

        try:
            for frame in decoder:
                metrics["decode_ms"] += (perf_counter() - previous) * 1000
                check()
                image = frame.image
                if writer is None:
                    store.set_timeline(job.job_id, decoder.timeline)
                    h, w = image.shape[:2]
                    with p.store._lock, p.store._connection:
                        p.store._connection.execute(
                            "UPDATE video_jobs SET width=?,height=? WHERE job_id=?",
                            (w, h, job.job_id),
                        )
                    writer = cv2.VideoWriter(
                        os.path.relpath(raw),
                        cv2.VideoWriter_fourcc(*"mp4v"),
                        job.metadata.fps,
                        (w, h),
                    )
                    if not writer.isOpened():
                        raise VideoProcessingError("output_initialization_failed")
                before = perf_counter()
                with p.progressive_inference_slots:
                    if model is not None:
                        try:
                            pairs = model.track(image)
                        except ModuleNotFoundError as e:
                            if e.name != "scipy":
                                raise
                            model = None
                    if model is None:
                        detections = p.detector.detect(image)
                        pairs = list(zip(detections, tracker.assign(detections), strict=True))
                metrics["inference_ms"] += (perf_counter() - before) * 1000
                before = perf_counter()
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
                if self.evidence:
                    prepared.extend(self.evidence.prepare(job, frame, pairs))
                metrics["evidence_ms"] += (perf_counter() - before) * 1000
                before = perf_counter()
                for d, tid in pairs:
                    if tid in boxes:
                        draw_box(image, boxes[tid], d.class_name)
                writer.write(image)
                count += 1
                metrics["render_ms"] += (perf_counter() - before) * 1000
                batch.append(
                    dict(
                        frame_index=frame.frame_index,
                        start_us=frame.start_us,
                        end_us=frame.end_us,
                        pts=str(frame.pts),
                        observations=observations,
                    )
                )
                if (
                    len(batch) >= p.progressive_batch_frames
                    or batch[-1]["end_us"] - batch[0]["start_us"] >= p.progressive_batch_us
                ):
                    publish()
                previous = perf_counter()
            publish()
            if count == 0:
                raise VideoProcessingError("invalid_video")
            metrics["analysis_ms"] = (perf_counter() - started) * 1000
            store.finish_analysis(job.job_id)
            writer.release()
            writer = None
            p.store.phase(job.job_id, "encoding", count)
            store.export(job.job_id, "encoding")
            p._encode_h264(
                raw,
                output,
                lambda: p.store.is_cancelled(job.job_id),
                started + p.timeout_seconds,
                job.expires_at,
            )
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
                    "UPDATE video_jobs SET status='completed',processing_phase='ready',output_path=?,actual_frame_count=?,total_frames=?,processed_frames=?,frame_total_confirmed=1,eligible_track_count=?,classes_present=? WHERE job_id=?",
                    (
                        str(output),
                        count,
                        count,
                        count,
                        eligible,
                        __import__("json").dumps(sorted(classes)),
                        job.job_id,
                    ),
                )
            store.export(job.job_id, "ready")
            return "completed"
        except Exception as exc:
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
            try:
                row = store.row(job.job_id)
                if row["analysis"] != "complete":
                    store.finish_analysis(job.job_id, code)
                store.export(job.job_id, "failed")
            except Exception:
                pass
            output.unlink(missing_ok=True)
            if isinstance(exc, VideoProcessingError):
                raise
            raise VideoProcessingError(code) from exc
        finally:
            if writer is not None:
                writer.release()
            raw.unlink(missing_ok=True)
            p.store.release(job.job_id)
            if self.evidence:
                self.evidence.discard_pending(job.job_id)
            p.logger.info(
                "progressive_video_outcome",
                extra={
                    "job_id": job.job_id,
                    "progress": count,
                    "elapsed_ms": round((perf_counter() - started) * 1000),
                    "inference_ms": round(metrics["inference_ms"]),
                    "output_ms": round(metrics["publish_ms"]),
                },
            )
