from __future__ import annotations

import sqlite3
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from app.api.error_handlers import ApiError
from app.domain.models import (
    CountEvent,
    CountJob,
    CountJobStatus,
    CountLine,
    CountPoint,
    CountSummary,
    may_transition_count,
)


class CountJobStore:
    """Thread-safe, temporary persistence for line-counting jobs and events."""

    def __init__(self, path: Path, ttl_seconds: int, max_queued: int) -> None:
        self.path = path
        self.ttl = timedelta(seconds=ttl_seconds)
        self.max_queued = max_queued
        path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        self._connection.executescript("""
            CREATE TABLE IF NOT EXISTS count_jobs (
              count_job_id TEXT PRIMARY KEY,
              source_video_job_id TEXT NOT NULL,
              owner_key_id TEXT NOT NULL,
              status TEXT NOT NULL,
              point_ax REAL NOT NULL, point_ay REAL NOT NULL,
              point_bx REAL NOT NULL, point_by REAL NOT NULL,
              processed_frames INTEGER NOT NULL DEFAULT 0,
              total_frames INTEGER NOT NULL,
              output_path TEXT,
              error_code TEXT,
              created_at TEXT NOT NULL, updated_at TEXT NOT NULL, expires_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_count_jobs_owner_expiry ON count_jobs(owner_key_id, expires_at);
            CREATE TABLE IF NOT EXISTS count_events (
              count_job_id TEXT NOT NULL,
              track_id INTEGER NOT NULL,
              class_id INTEGER NOT NULL,
              class_name TEXT NOT NULL,
              direction TEXT NOT NULL CHECK(direction IN ('A_to_B', 'B_to_A')),
              frame_index INTEGER NOT NULL,
              video_time_seconds REAL NOT NULL,
              PRIMARY KEY(count_job_id, track_id)
            );
            CREATE INDEX IF NOT EXISTS idx_count_events_page ON count_events(count_job_id, frame_index, track_id);
            CREATE TABLE IF NOT EXISTS expired_count_jobs (
              count_job_id TEXT NOT NULL, owner_key_id TEXT NOT NULL, expired_at TEXT NOT NULL,
              PRIMARY KEY(count_job_id, owner_key_id)
            );
        """)
        self._connection.commit()
        self.recover()

    def create(
        self, source_video_job_id: str, owner_key_id: str, line: CountLine, total_frames: int, source_expires_at: datetime
    ) -> CountJob:
        with self._lock:
            self.cleanup()
            queued = self._connection.execute("SELECT count(*) FROM count_jobs WHERE status='queued'").fetchone()[0]
            if queued >= self.max_queued:
                raise ApiError(503, "count_queue_full", "The count queue is currently full.")
            now = datetime.now(UTC)
            expires_at = min(source_expires_at, now + self.ttl)
            count_job_id = str(uuid4())
            self._connection.execute(
                """INSERT INTO count_jobs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    count_job_id, source_video_job_id, owner_key_id, CountJobStatus.QUEUED.value,
                    line.point_a.x, line.point_a.y, line.point_b.x, line.point_b.y, 0, total_frames,
                    None, None, now.isoformat(), now.isoformat(), expires_at.isoformat(),
                ),
            )
            self._connection.commit()
        return self.get(count_job_id, owner_key_id)

    def get(self, count_job_id: str, owner_key_id: str) -> CountJob:
        self.cleanup()
        row = self._connection.execute(
            "SELECT * FROM count_jobs WHERE count_job_id=? AND owner_key_id=?", (count_job_id, owner_key_id)
        ).fetchone()
        if row is None:
            expired = self._connection.execute(
                "SELECT 1 FROM expired_count_jobs WHERE count_job_id=? AND owner_key_id=?", (count_job_id, owner_key_id)
            ).fetchone()
            if expired:
                raise ApiError(410, "count_job_expired", "The count result has expired.")
            raise ApiError(404, "count_job_not_found", "No accessible count job was found.")
        return self._row(row)

    def dequeue(self) -> CountJob | None:
        with self._lock:
            self.cleanup()
            row = self._connection.execute(
                "SELECT * FROM count_jobs WHERE status='queued' ORDER BY created_at LIMIT 1"
            ).fetchone()
            if row is None:
                return None
            now = datetime.now(UTC).isoformat()
            changed = self._connection.execute(
                "UPDATE count_jobs SET status='processing', updated_at=? WHERE count_job_id=? AND status='queued'",
                (now, row["count_job_id"]),
            ).rowcount
            self._connection.commit()
            if not changed:
                return None
            return self._row(self._connection.execute(
                "SELECT * FROM count_jobs WHERE count_job_id=?", (row["count_job_id"],)
            ).fetchone())

    def progress(self, count_job_id: str, processed_frames: int) -> None:
        with self._lock:
            self._connection.execute(
                """UPDATE count_jobs SET processed_frames=MAX(processed_frames, ?), updated_at=?
                   WHERE count_job_id=? AND status='processing'""",
                (processed_frames, datetime.now(UTC).isoformat(), count_job_id),
            )
            self._connection.commit()

    def record_event(self, event: CountEvent) -> bool:
        with self._lock:
            inserted = self._connection.execute(
                """INSERT OR IGNORE INTO count_events
                   (count_job_id, track_id, class_id, class_name, direction, frame_index, video_time_seconds)
                   VALUES (?,?,?,?,?,?,?)""",
                (event.count_job_id, event.track_id, event.class_id, event.class_name, event.direction,
                 event.frame_index, event.video_time_seconds),
            ).rowcount
            self._connection.commit()
            return bool(inserted)

    def events(self, count_job_id: str, owner_key_id: str, page: int, page_size: int) -> tuple[list[CountEvent], int]:
        self.get(count_job_id, owner_key_id)
        total = self._connection.execute(
            "SELECT count(*) FROM count_events WHERE count_job_id=?", (count_job_id,)
        ).fetchone()[0]
        rows = self._connection.execute(
            """SELECT * FROM count_events WHERE count_job_id=? ORDER BY frame_index, track_id LIMIT ? OFFSET ?""",
            (count_job_id, page_size, (page - 1) * page_size),
        ).fetchall()
        return [self._event(row) for row in rows], total

    def summary(self, count_job_id: str, owner_key_id: str) -> list[CountSummary]:
        self.get(count_job_id, owner_key_id)
        rows = self._connection.execute(
            """SELECT class_name, direction, count(*) AS total FROM count_events WHERE count_job_id=?
               GROUP BY class_name, direction ORDER BY class_name, direction""",
            (count_job_id,),
        ).fetchall()
        return [CountSummary(row["class_name"], row["direction"], row["total"]) for row in rows]

    def all_events(self, count_job_id: str, owner_key_id: str) -> list[CountEvent]:
        return self.events(count_job_id, owner_key_id, 1, 1_000_000)[0]

    def is_active(self, count_job_id: str) -> bool:
        """Return whether a worker may still publish progress or an artifact for this job."""
        row = self._connection.execute(
            "SELECT status, expires_at FROM count_jobs WHERE count_job_id=?", (count_job_id,)
        ).fetchone()
        return (
            row is not None
            and row["status"] == CountJobStatus.PROCESSING.value
            and datetime.fromisoformat(row["expires_at"]) > datetime.now(UTC)
        )

    def finish(self, count_job_id: str, output_path: Path) -> bool:
        """Publish an artifact only while the job remains processing and unexpired."""
        with self._lock:
            changed = self._connection.execute(
                """UPDATE count_jobs SET status='completed', output_path=?, processed_frames=total_frames, updated_at=?
                   WHERE count_job_id=? AND status='processing' AND expires_at>?""",
                (str(output_path), datetime.now(UTC).isoformat(), count_job_id, datetime.now(UTC).isoformat()),
            ).rowcount
            self._connection.commit()
            return bool(changed)

    def fail(self, count_job_id: str, error_code: str) -> None:
        with self._lock:
            self._connection.execute("DELETE FROM count_events WHERE count_job_id=?", (count_job_id,))
            self._connection.execute(
                """UPDATE count_jobs SET status='failed', error_code=?, updated_at=?
                   WHERE count_job_id=? AND status='processing'""",
                (error_code, datetime.now(UTC).isoformat(), count_job_id),
            )
            self._connection.commit()

    def cancel(self, count_job_id: str, owner_key_id: str) -> CountJob:
        job = self.get(count_job_id, owner_key_id)
        if not may_transition_count(job.status, CountJobStatus.CANCELLED):
            raise ApiError(409, "count_job_terminal", "The count job is already terminal.")
        self._connection.execute("DELETE FROM count_events WHERE count_job_id=?", (count_job_id,))
        self._connection.execute(
            "UPDATE count_jobs SET status='cancelled', updated_at=? WHERE count_job_id=?",
            (datetime.now(UTC).isoformat(), count_job_id),
        )
        self._connection.commit()
        return self.get(count_job_id, owner_key_id)

    def is_cancelled(self, count_job_id: str) -> bool:
        row = self._connection.execute("SELECT status FROM count_jobs WHERE count_job_id=?", (count_job_id,)).fetchone()
        return row is not None and row["status"] == CountJobStatus.CANCELLED.value

    def recover(self) -> None:
        now = datetime.now(UTC).isoformat()
        self._connection.execute(
            "UPDATE count_jobs SET status='queued', updated_at=? WHERE status='processing' AND expires_at>?", (now, now)
        )
        self._connection.commit()

    def cleanup(self) -> list[Path]:
        with self._lock:
            now = datetime.now(UTC).isoformat()
            expired = self._connection.execute(
                "SELECT count_job_id, owner_key_id, output_path FROM count_jobs WHERE expires_at<=?",
                (now,),
            ).fetchall()
            if not expired:
                return []
            self._connection.executemany("DELETE FROM count_events WHERE count_job_id=?", [(row["count_job_id"],) for row in expired])
            self._connection.executemany(
                "INSERT OR REPLACE INTO expired_count_jobs VALUES (?,?,?)",
                [(row["count_job_id"], row["owner_key_id"], now) for row in expired],
            )
            self._connection.execute("DELETE FROM count_jobs WHERE expires_at<=?", (now,))
            self._connection.commit()
            return [Path(row["output_path"]) for row in expired if row["output_path"]]

    def close(self) -> None:
        self._connection.close()

    @staticmethod
    def _row(row: sqlite3.Row) -> CountJob:
        return CountJob(
            row["count_job_id"], row["source_video_job_id"], row["owner_key_id"], CountJobStatus(row["status"]),
            CountLine(CountPoint(row["point_ax"], row["point_ay"]), CountPoint(row["point_bx"], row["point_by"])),
            datetime.fromisoformat(row["created_at"]), datetime.fromisoformat(row["updated_at"]),
            datetime.fromisoformat(row["expires_at"]), row["total_frames"], row["processed_frames"],
            Path(row["output_path"]) if row["output_path"] else None, row["error_code"],
        )

    @staticmethod
    def _event(row: sqlite3.Row) -> CountEvent:
        return CountEvent(
            row["count_job_id"], row["track_id"], row["class_id"], row["class_name"], row["direction"],
            row["frame_index"], row["video_time_seconds"],
        )
