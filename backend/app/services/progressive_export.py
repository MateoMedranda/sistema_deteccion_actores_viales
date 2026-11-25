"""Explicit, bounded export of persisted annotations. Never runs inference."""
from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from pathlib import Path
import threading
from time import perf_counter
import cv2
from app.api.error_handlers import ApiError
from app.adapters.timed_video_decoder import TimedVideoDecoder
from app.services.video_presentation import draw_box
from app.services.video_processing import VideoProcessor


class ProgressiveExport:
    def __init__(self, store, legacy, artifacts, settings, logger):
        self.store, self.legacy, self.artifacts = store, legacy, artifacts
        self.settings, self.logger = settings, logger
        from app.services.video_export_variant_store import VideoExportVariantStore
        self.variants=VideoExportVariantStore(store,settings)
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self.run, name="video-export", daemon=True)
        self.encoder = VideoProcessor(None, legacy, artifacts, settings.ffmpeg_executable,
                                      settings.video_job_timeout_seconds, logger)._encode_h264
        with store.lock, store.db:
            store.db.execute("""CREATE TABLE IF NOT EXISTS p_video_exports(
                job TEXT PRIMARY KEY,state TEXT NOT NULL,frames INTEGER NOT NULL DEFAULT 0,
                error TEXT,output TEXT,temporary TEXT)""")
            interrupted = store.db.execute("SELECT job,output,temporary FROM p_video_exports WHERE state IN ('rendering','encoding')").fetchall()
            for row in interrupted:
                for path in (row["output"], row["temporary"]):
                    if path:
                        try: Path(path).unlink(missing_ok=True)
                        except OSError: pass
                store.db.execute("UPDATE p_video_exports SET state='failed',error='export_interrupted' WHERE job=?", (row["job"],))
                store.db.execute("UPDATE p_video SET export='failed' WHERE job=?", (row["job"],))
                store.db.execute("UPDATE video_jobs SET output_path=NULL WHERE job_id=?", (row["job"],))

    def start(self):
        self.thread.start()

    def close(self):
        self.stop.set()
        self.thread.join()

    def status(self, job, owner, renderer=None):
        if renderer:return self.variants.status(job,owner,renderer)
        with self.store.lock:
            row = self.store.row(job, owner)
            parent = self.legacy.get(job, owner)
            record = self.store.db.execute("SELECT * FROM p_video_exports WHERE job=?", (job,)).fetchone()
            ready = parent.output_path is not None and parent.output_path.is_file() and (record is None or record["state"] == "ready")
            state = "ready" if ready else record["state"] if record and record["state"] != "ready" else "waiting"
            return dict(job_id=job, state=state, processed_frames=row["frames"] if ready else record["frames"] if record else 0,
                        total_frames=row["frames"], expires_at=row["expires"],
                        url=f"/api/v1/video-jobs/{job}/annotated-video/content" if ready else None,
                        error_code=record["error"] if record else None)

    def request(self, job, owner, renderer=None):
        if renderer:
            if self.stop.is_set():raise ApiError(503,"export_unavailable","Export is unavailable.")
            return self.variants.request(job,owner,renderer)
        with self.store.lock:
            row = self.store.row(job, owner)
            if row["analysis"] != "complete":
                raise ApiError(409, "analysis_not_ready", "Complete the analysis before exporting.")
            current = self.status(job, owner)
            if current["state"] in ("queued", "rendering", "encoding", "ready"):
                return current
            if self.stop.is_set():
                raise ApiError(503, "export_unavailable", "Export is temporarily unavailable.")
            queued = self.store.db.execute("SELECT count(*) FROM p_video_exports WHERE state='queued'").fetchone()[0]
            if queued >= self.settings.max_queued_video_jobs:
                raise ApiError(503, "export_queue_full", "The export queue is full.")
            with self.store.db:
                self.store.db.execute("""INSERT INTO p_video_exports(job,state) VALUES(?,'queued')
                    ON CONFLICT(job) DO UPDATE SET state='queued',frames=0,error=NULL""", (job,))
                self.store.db.execute("UPDATE p_video SET export='queued' WHERE job=?", (job,))
                self.store.db.execute("UPDATE video_jobs SET output_path=NULL WHERE job_id=?", (job,))
            return self.status(job, owner)

    def claim(self):
        with self.store.lock, self.store.db:
            # Prefer analysis already queued/running; exports only start on explicit intent.
            if self.store.db.execute("SELECT 1 FROM video_jobs WHERE status IN ('queued','processing') LIMIT 1").fetchone():
                return None
            row = self.store.db.execute("""SELECT e.job,v.owner FROM p_video_exports e JOIN p_video v ON v.job=e.job
                WHERE e.state='queued' AND v.analysis='complete' AND v.retired=0 AND v.expires>?
                ORDER BY e.rowid LIMIT 1""", (datetime.now(UTC).isoformat(),)).fetchone()
            if row:
                self.store.db.execute("UPDATE p_video_exports SET state='rendering' WHERE job=?", (row["job"],))
                self.store.db.execute("UPDATE p_video SET export='encoding' WHERE job=?", (row["job"],))
                return row["job"], row["owner"]
        return self.variants.claim()

    def run(self):
        while not self.stop.wait(.25):
            claimed = self.claim()
            if claimed:
                self.process(*claimed)

    def process(self, job, owner, renderer=None):
        table="p_video_label_exports" if renderer else "p_video_exports"
        started = perf_counter()
        metrics = dict(decode_ms=0.0, annotation_ms=0.0, video_write_ms=0.0, encode_ms=0.0)
        writer = frames = None
        output = raw = None
        leases = []
        count, outcome, code = 0, "failed", None

        def check():
            if self.stop.is_set():
                raise RuntimeError("export_interrupted")
            if perf_counter() - started >= self.settings.video_job_timeout_seconds:
                raise RuntimeError("export_timeout")
            with self.store.lock:
                row = self.store.row(job, owner)
                if row["analysis"] != "complete":
                    raise RuntimeError("export_unavailable")

        def cancelled():
            try: check()
            except Exception: return True
            return False

        try:
            check()
            with self.store.lock, self.store.db:
                row = self.store.row(job, owner)
                parent = self.legacy.get(job, owner)
                record = self.store.db.execute(f"SELECT * FROM {table} WHERE job=?", (job,)).fetchone()
                output = Path(record["output"]) if record["output"] else self.artifacts.annotated_output_path()
                raw = Path(record["temporary"]) if record["temporary"] else output.with_suffix(".raw.mp4")
                source, total = Path(row["source"]), row["frames"]
                self.store.db.execute(f"UPDATE {table} SET output=?,temporary=? WHERE job=?", (str(output), str(raw), job))
                for path in (source, raw, output):
                    key = str(path)
                    self.store.readers[key] = self.store.readers.get(key, 0) + 1
                    leases.append(key)
            frames = iter(TimedVideoDecoder(source))
            while True:
                before = perf_counter()
                try: frame = next(frames)
                except StopIteration: break
                metrics["decode_ms"] += (perf_counter() - before) * 1000
                check()
                with self.store.lock:
                    stored = self.store.db.execute("SELECT payload FROM p_frames WHERE job=? AND idx=?", (job, frame.frame_index)).fetchone()
                receipt = json.loads(stored[0]) if stored else None
                if not receipt or (receipt["start_us"], receipt["end_us"]) != (frame.start_us, frame.end_us):
                    raise RuntimeError("export_timeline_mismatch")
                image = frame.image
                if writer is None:
                    h, w = image.shape[:2]
                    writer = cv2.VideoWriter(os.path.relpath(raw), cv2.VideoWriter_fourcc(*"mp4v"), parent.metadata.fps, (w, h))
                    if not writer.isOpened():
                        raise RuntimeError("export_initialization_failed")
                before = perf_counter()
                if renderer:
                    from app.services.video_export_labels import draw_labels
                    draw_labels(image,receipt['observations'])
                else:
                    for ob in receipt["observations"]:
                        box = ob["display_bbox"]
                        if box:
                            draw_box(image, tuple(box[key] for key in ("x_min", "y_min", "x_max", "y_max")), ob["class_name"])
                metrics["annotation_ms"] += (perf_counter() - before) * 1000
                before = perf_counter()
                writer.write(image)
                metrics["video_write_ms"] += (perf_counter() - before) * 1000
                count += 1
                if count % 15 == 0:
                    with self.store.lock, self.store.db:
                        self.store.db.execute(f"UPDATE {table} SET frames=? WHERE job=?", (count, job))
            if count != total or not count:
                raise RuntimeError("export_timeline_mismatch")
            writer.release()
            writer = None
            with self.store.lock, self.store.db:
                self.store.db.execute(f"UPDATE {table} SET state='encoding',frames=? WHERE job=?", (count, job))
            before = perf_counter()
            try:
                self.encoder(raw, output, cancelled, started + self.settings.video_job_timeout_seconds, parent.expires_at)
            finally:
                metrics["encode_ms"] = (perf_counter() - before) * 1000
            check()
            if not output.is_file():
                raise RuntimeError("export_encoding_failed")
            with self.store.lock, self.store.db:
                self.store.row(job, owner)
                if not renderer:self.store.db.execute("UPDATE video_jobs SET output_path=? WHERE job_id=? AND status='completed'", (str(output), job))
                self.store.db.execute(f"UPDATE {table} SET state='ready',error=NULL WHERE job=?", (job,))
                if not renderer:self.store.db.execute("UPDATE p_video SET export='ready' WHERE job=?", (job,))
            outcome = "ready"
        except Exception as exc:
            allowed = {"export_interrupted", "export_timeout", "export_unavailable", "export_timeline_mismatch", "export_initialization_failed", "export_label_layout_unrepresentable"}
            code = str(exc) if str(exc) in allowed else "export_failed"
            with self.store.lock, self.store.db:
                self.store.db.execute(f"UPDATE {table} SET state='failed',error=? WHERE job=?", (code, job))
                if not renderer:self.store.db.execute("UPDATE p_video SET export='failed' WHERE job=?", (job,))
            self.logger.error("video_export_failed", extra={"job_id": job, "error_code": code, "exception_type": type(exc).__name__})
        finally:
            if frames is not None: frames.close()
            if writer is not None: writer.release()
            for path in (raw, output if outcome != "ready" else None):
                if path:
                    try: path.unlink(missing_ok=True)
                    except OSError: pass
            with self.store.lock:
                for key in leases:
                    self.store.readers[key] -= 1
                    if not self.store.readers[key]: del self.store.readers[key]
            self.logger.info("video_export_outcome", extra={"job_id": job, "status": outcome, "progress": count,
                "elapsed_ms": round((perf_counter()-started)*1000), "error_code": code})
            # Export timing is intentionally separate from the analysis profile.
            try:
                directory = self.settings.video_job_db_path.parent / "video-export-profiles"
                directory.mkdir(parents=True, exist_ok=True)
                path = directory / (job + ("."+renderer if renderer else "") + ".json")
                temporary = path.with_suffix(".json.tmp")
                temporary.write_text(json.dumps(dict(job_id=job, renderer_version=renderer, outcome=outcome, frames=count,
                    error_code=code, total_ms=round((perf_counter()-started)*1000), **metrics), indent=2), encoding="utf-8")
                temporary.replace(path)
            except OSError:
                self.logger.warning("video_export_profile_failed", extra={"job_id": job})
