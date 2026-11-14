from __future__ import annotations

import sqlite3
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from app.api.error_handlers import ApiError
from app.domain.models import (
    FrameDetection,
    VideoJob,
    VideoJobStatus,
    VideoMetadata,
    VIDEO_TERMINAL_STATES,
    may_transition,
)


class VideoJobStore:
    def __init__(self, path: Path, ttl_seconds: int, max_queued: int) -> None:
        self.path, self.ttl, self.max_queued = path, timedelta(seconds=ttl_seconds), max_queued
        path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        self._connection.execute("""CREATE TABLE IF NOT EXISTS video_jobs (
          job_id TEXT PRIMARY KEY, owner_key_id TEXT NOT NULL, status TEXT NOT NULL, media_type TEXT NOT NULL,
          container TEXT NOT NULL, codec TEXT NOT NULL, size_bytes INTEGER NOT NULL, duration REAL NOT NULL,
          width INTEGER NOT NULL, height INTEGER NOT NULL, fps REAL NOT NULL, total_frames INTEGER NOT NULL,
          staged_path TEXT, output_path TEXT, processed_frames INTEGER NOT NULL DEFAULT 0, error_code TEXT,
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL, expires_at TEXT NOT NULL)""")
        self._connection.execute("""CREATE TABLE IF NOT EXISTS video_detections (
          job_id TEXT NOT NULL, frame_index INTEGER NOT NULL, track_id INTEGER NOT NULL,
          class_id INTEGER NOT NULL, class_name TEXT NOT NULL, confidence REAL NOT NULL,
          x_min INTEGER NOT NULL, y_min INTEGER NOT NULL, x_max INTEGER NOT NULL, y_max INTEGER NOT NULL,
          PRIMARY KEY(job_id, frame_index, track_id, class_id))""")
        self._connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_video_detections_page ON video_detections(job_id, frame_index, track_id)"
        )
        self._connection.execute("""CREATE TABLE IF NOT EXISTS expired_video_jobs (
          job_id TEXT NOT NULL, owner_key_id TEXT NOT NULL, expired_at TEXT NOT NULL,
          PRIMARY KEY(job_id, owner_key_id))""")
        self._connection.commit()
        self.recover()

    def create(self, owner_key_id: str, metadata: VideoMetadata, staged_path: Path) -> VideoJob:
        with self._lock:
            self.cleanup()
            queued = self._connection.execute("SELECT count(*) FROM video_jobs WHERE status='queued'").fetchone()[0]
            if queued >= self.max_queued:
                raise ApiError(503, "queue_full", "The video queue is currently full.")
            now = datetime.now(UTC); job_id = str(uuid4()); expires = now + self.ttl
            self._connection.execute("INSERT INTO video_jobs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                job_id, owner_key_id, "queued", metadata.media_type, metadata.container, metadata.codec,
                metadata.size_bytes, metadata.duration_seconds, metadata.width, metadata.height, metadata.fps,
                metadata.total_frames, str(staged_path), None, 0, None, now.isoformat(), now.isoformat(), expires.isoformat()))
            self._connection.commit()
        return self.get(job_id, owner_key_id)

    def get(self, job_id: str, owner_key_id: str) -> VideoJob:
        self.cleanup(); row = self._connection.execute("SELECT * FROM video_jobs WHERE job_id=? AND owner_key_id=?", (job_id, owner_key_id)).fetchone()
        if row is None:
            expired = self._connection.execute(
                "SELECT 1 FROM expired_video_jobs WHERE job_id=? AND owner_key_id=?", (job_id, owner_key_id)
            ).fetchone()
            if expired:
                raise ApiError(410, "job_expired", "The video job has expired.")
            raise ApiError(404, "job_not_found", "No accessible video job was found.")
        return self._row(row)

    def cancel(self, job_id: str, owner_key_id: str) -> VideoJob:
        job = self.get(job_id, owner_key_id)
        if not may_transition(job.status, VideoJobStatus.CANCELLED): raise ApiError(409, "job_terminal", "The video job is already terminal.")
        self._connection.execute("UPDATE video_jobs SET status='cancelled', updated_at=? WHERE job_id=?", (datetime.now(UTC).isoformat(), job_id)); self._connection.commit()
        return self.get(job_id, owner_key_id)

    def dequeue(self) -> VideoJob | None:
        """Claim the oldest queued job.  The lock keeps one in-process worker from double claiming it."""
        with self._lock:
            self.cleanup()
            row = self._connection.execute(
                "SELECT * FROM video_jobs WHERE status='queued' ORDER BY created_at LIMIT 1"
            ).fetchone()
            if row is None:
                return None
            now = datetime.now(UTC).isoformat()
            changed = self._connection.execute(
                "UPDATE video_jobs SET status='processing', updated_at=? WHERE job_id=? AND status='queued'",
                (now, row["job_id"]),
            ).rowcount
            self._connection.commit()
            if not changed:
                return None
            return self._row(self._connection.execute("SELECT * FROM video_jobs WHERE job_id=?", (row["job_id"],)).fetchone())

    def progress(self, job_id: str, processed_frames: int) -> None:
        with self._lock:
            self._connection.execute(
                "UPDATE video_jobs SET processed_frames=?, updated_at=? WHERE job_id=? AND status='processing'",
                (processed_frames, datetime.now(UTC).isoformat(), job_id),
            )
            self._connection.commit()

    def is_cancelled(self, job_id: str) -> bool:
        row = self._connection.execute("SELECT status FROM video_jobs WHERE job_id=?", (job_id,)).fetchone()
        return row is not None and row["status"] == VideoJobStatus.CANCELLED.value

    def finish(self, job_id: str, output_path: Path, detections: list[FrameDetection]) -> None:
        with self._lock:
            if self.is_cancelled(job_id):
                return
            self._connection.executemany(
                "INSERT OR REPLACE INTO video_detections VALUES (?,?,?,?,?,?,?,?,?,?)",
                [(job_id, d.frame_index, d.track_id, d.class_id, d.class_name, d.confidence,
                  d.x_min, d.y_min, d.x_max, d.y_max) for d in detections],
            )
            self._connection.execute(
                "UPDATE video_jobs SET status='completed', output_path=?, processed_frames=total_frames, updated_at=? WHERE job_id=? AND status='processing'",
                (str(output_path), datetime.now(UTC).isoformat(), job_id),
            )
            self._connection.commit()

    def fail(self, job_id: str, error_code: str) -> None:
        with self._lock:
            self._connection.execute(
                "UPDATE video_jobs SET status='failed', error_code=?, updated_at=? WHERE job_id=? AND status='processing'",
                (error_code, datetime.now(UTC).isoformat(), job_id),
            )
            self._connection.commit()

    def detections(self, job_id: str, owner_key_id: str, page: int, page_size: int) -> tuple[list[FrameDetection], int]:
        job = self.get(job_id, owner_key_id)
        if job.status is not VideoJobStatus.COMPLETED:
            raise ApiError(409, "result_not_ready", "The video result is not available yet.")
        total = self._connection.execute("SELECT count(*) FROM video_detections WHERE job_id=?", (job_id,)).fetchone()[0]
        rows = self._connection.execute(
            "SELECT * FROM video_detections WHERE job_id=? ORDER BY frame_index, track_id LIMIT ? OFFSET ?",
            (job_id, page_size, (page - 1) * page_size),
        ).fetchall()
        return [FrameDetection(row["frame_index"], row["track_id"], row["class_id"], row["class_name"], row["confidence"], row["x_min"], row["y_min"], row["x_max"], row["y_max"]) for row in rows], total

    def summary(self, job_id: str, owner_key_id: str) -> dict[str, int]:
        job = self.get(job_id, owner_key_id)
        if job.status is not VideoJobStatus.COMPLETED:
            raise ApiError(409, "result_not_ready", "The video result is not available yet.")
        rows = self._connection.execute(
            "SELECT class_name, count(*) AS total FROM video_detections WHERE job_id=? GROUP BY class_name ORDER BY class_name",
            (job_id,),
        ).fetchall()
        return {row["class_name"]: row["total"] for row in rows}

    def all_detections(self, job_id: str, owner_key_id: str) -> list[FrameDetection]:
        """Return completed source detections for downstream analytics without reinference."""
        job = self.get(job_id, owner_key_id)
        if job.status is not VideoJobStatus.COMPLETED:
            raise ApiError(409, "source_not_ready", "The source video is not available for counting.")
        rows = self._connection.execute(
            "SELECT * FROM video_detections WHERE job_id=? ORDER BY frame_index, track_id", (job_id,)
        ).fetchall()
        return [FrameDetection(
            row["frame_index"], row["track_id"], row["class_id"], row["class_name"], row["confidence"],
            row["x_min"], row["y_min"], row["x_max"], row["y_max"],
        ) for row in rows]

    def recover(self) -> None:
        now = datetime.now(UTC).isoformat()
        self._connection.execute("UPDATE video_jobs SET status='queued', updated_at=? WHERE status='processing' AND expires_at>?", (now, now)); self._connection.commit()

    def cleanup(self) -> list[Path]:
        with self._lock:
            expired = self._connection.execute(
                "SELECT job_id, owner_key_id, staged_path, output_path FROM video_jobs WHERE expires_at<=?",
                (datetime.now(UTC).isoformat(),),
            ).fetchall()
            self._connection.executemany("DELETE FROM video_detections WHERE job_id=?", [(row["job_id"],) for row in expired])
            self._connection.executemany(
                "INSERT OR REPLACE INTO expired_video_jobs VALUES (?,?,?)",
                [(row["job_id"], row["owner_key_id"], datetime.now(UTC).isoformat()) for row in expired],
            )
            self._connection.execute("DELETE FROM video_jobs WHERE expires_at<=?", (datetime.now(UTC).isoformat(),)); self._connection.commit()
            return [Path(value) for row in expired for value in (row["staged_path"], row["output_path"]) if value]

    def close(self) -> None: self._connection.close()

    @staticmethod
    def _row(row: sqlite3.Row) -> VideoJob:
        metadata = VideoMetadata(row["media_type"], row["container"], row["codec"], row["size_bytes"], row["duration"], row["width"], row["height"], row["fps"], row["total_frames"])
        return VideoJob(row["job_id"], row["owner_key_id"], VideoJobStatus(row["status"]), metadata, datetime.fromisoformat(row["created_at"]), datetime.fromisoformat(row["updated_at"]), datetime.fromisoformat(row["expires_at"]), Path(row["staged_path"]) if row["staged_path"] else None, Path(row["output_path"]) if row["output_path"] else None, row["processed_frames"], row["error_code"])
