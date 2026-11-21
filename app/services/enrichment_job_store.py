from __future__ import annotations

import json
import sqlite3
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from app.api.error_handlers import ApiError
from app.services.enrichment_results import normalize_results
from app.domain.models import EnrichmentJob, EnrichmentJobStatus, ENRICHMENT_TRANSITIONS


class EnrichmentJobStore:
    """SQLite-backed temporary job metadata and redacted-at-expiry results."""
    def __init__(self, path: Path, ttl_seconds: int, max_queued: int, clock=None) -> None:
        self.clock = clock or (lambda: datetime.now(UTC))
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.ttl, self.max_queued, self.lock = timedelta(seconds=ttl_seconds), max_queued, threading.RLock()
        self.connection.execute("""CREATE TABLE IF NOT EXISTS enrichment_jobs (
          enrichment_job_id TEXT PRIMARY KEY, source_kind TEXT NOT NULL, source_id TEXT NOT NULL,
          owner_key_id TEXT NOT NULL, status TEXT NOT NULL, total_units INTEGER NOT NULL,
          processed_units INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
          expires_at TEXT NOT NULL, error_code TEXT, results_json TEXT NOT NULL DEFAULT '[]')""")
        self.connection.execute("CREATE INDEX IF NOT EXISTS idx_enrichment_owner_expiry ON enrichment_jobs(owner_key_id, expires_at)")
        self.connection.execute("""CREATE TABLE IF NOT EXISTS expired_enrichment_jobs (
          enrichment_job_id TEXT NOT NULL, owner_key_id TEXT NOT NULL, expired_at TEXT NOT NULL,
          PRIMARY KEY(enrichment_job_id, owner_key_id))""")
        self.connection.executescript("""
          CREATE TABLE IF NOT EXISTS enrichment_units (
            unit_id TEXT PRIMARY KEY, enrichment_job_id TEXT NOT NULL, detection_id INTEGER NOT NULL,
            track_id INTEGER, class_id INTEGER NOT NULL, class_name TEXT NOT NULL, evidence_json TEXT NOT NULL);
          CREATE UNIQUE INDEX IF NOT EXISTS idx_enrichment_track_once ON enrichment_units(enrichment_job_id, track_id) WHERE track_id IS NOT NULL;
          CREATE TABLE IF NOT EXISTS enrichment_attributes (
            unit_id TEXT NOT NULL, attribute_name TEXT NOT NULL, label TEXT NOT NULL, confidence REAL NOT NULL,
            evidence_frame_index INTEGER, manifest_version TEXT, PRIMARY KEY(unit_id, attribute_name));
          CREATE TABLE IF NOT EXISTS enrichment_plates (
            unit_id TEXT PRIMARY KEY, status TEXT NOT NULL, plate_text TEXT, localizer_confidence REAL,
            ocr_confidence REAL, used_enhancement INTEGER NOT NULL, evidence_json TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS enrichment_plate_candidates (
            unit_id TEXT NOT NULL, frame_index INTEGER, text TEXT, localizer_confidence REAL, ocr_confidence REAL,
            quality REAL, PRIMARY KEY(unit_id, frame_index, text));
        """)
        self.connection.commit(); self.recover()

    def create(self, source_kind, source_id, owner_key_id, total_units, source_expires_at):
        with self.lock, self.connection:
            self.cleanup()
            queued = self.connection.execute("SELECT count(*) FROM enrichment_jobs WHERE status='queued'").fetchone()[0]
            if queued >= self.max_queued:
                raise ApiError(503, "queue_full", "The enrichment queue is currently full.")
            now = self.clock()
            expiry = min(source_expires_at, now + self.ttl)
            if expiry <= now:
                raise ApiError(410, "source_expired", "The requested source has expired.")
            job_id = str(uuid4())
            self.connection.execute("INSERT INTO enrichment_jobs VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (
                job_id, source_kind, source_id, owner_key_id, "queued", total_units, 0,
                now.isoformat(), now.isoformat(), expiry.isoformat(), None, "[]"))
            return self._row(self.connection.execute("SELECT * FROM enrichment_jobs WHERE enrichment_job_id=?", (job_id,)).fetchone())

    def get(self, job_id, owner_key_id):
        with self.lock:
            self.cleanup()
            row = self.connection.execute("SELECT * FROM enrichment_jobs WHERE enrichment_job_id=? AND owner_key_id=?", (job_id, owner_key_id)).fetchone()
            if row is None:
                expired = self.connection.execute("SELECT 1 FROM expired_enrichment_jobs WHERE enrichment_job_id=? AND owner_key_id=?", (job_id, owner_key_id)).fetchone()
                if expired:
                    raise ApiError(410, "job_expired", "The enrichment job has expired.")
                raise ApiError(404, "job_not_found", "No accessible enrichment job was found.")
            return self._row(row)

    def dequeue(self):
        with self.lock, self.connection:
            self.cleanup()
            row = self.connection.execute("SELECT * FROM enrichment_jobs WHERE status='queued' ORDER BY created_at, enrichment_job_id LIMIT 1").fetchone()
            if row is None:
                return None
            self.connection.execute("UPDATE enrichment_jobs SET status='processing', updated_at=? WHERE enrichment_job_id=? AND status='queued'", (self.clock().isoformat(), row['enrichment_job_id']))
            return self._row(self.connection.execute("SELECT * FROM enrichment_jobs WHERE enrichment_job_id=?", (row['enrichment_job_id'],)).fetchone())

    def _active_row(self, job_id):
        row = self.connection.execute("SELECT * FROM enrichment_jobs WHERE enrichment_job_id=?", (job_id,)).fetchone()
        if row is None or row['status'] != 'processing' or datetime.fromisoformat(row['expires_at']) <= self.clock():
            return None
        return row

    def is_processing(self, job_id):
        with self.lock:
            return self._active_row(job_id) is not None

    def finish(self, job_id, results) -> str:
        # Snapshot the outcome under the same lock as publication.
        with self.lock, self.connection:
            row = self._active_row(job_id)
            if row is None:
                self.cleanup()
                current = self.connection.execute(
                    "SELECT status FROM enrichment_jobs WHERE enrichment_job_id=?",
                    (job_id,),
                ).fetchone()
                return current["status"] if current is not None else "expired"
            clean = normalize_results(results)
            if len(clean) != row['total_units']:
                raise ValueError('incomplete_results')
            self._delete_results(job_id)
            self._persist_results(job_id, clean)
            if datetime.fromisoformat(row['expires_at']) <= self.clock():
                self.cleanup()
                return "expired"
            self.connection.execute("UPDATE enrichment_jobs SET status='completed', processed_units=total_units, results_json=?, updated_at=? WHERE enrichment_job_id=? AND status='processing'", (json.dumps(clean), self.clock().isoformat(), job_id))
            return "completed"

    def progress(self, job_id, processed_units):
        with self.lock, self.connection:
            if self._active_row(job_id) is not None:
                self.connection.execute("UPDATE enrichment_jobs SET processed_units=MIN(total_units, MAX(processed_units, ?)), updated_at=? WHERE enrichment_job_id=?", (processed_units, self.clock().isoformat(), job_id))

    def fail(self, job_id, error_code):
        with self.lock, self.connection:
            if self._active_row(job_id) is not None:
                self._delete_results(job_id)
                self.connection.execute("UPDATE enrichment_jobs SET status='failed', error_code=?, results_json='[]', updated_at=? WHERE enrichment_job_id=?", (error_code, self.clock().isoformat(), job_id))

    def cancel(self, job_id, owner_key_id):
        with self.lock, self.connection:
            job = self.get(job_id, owner_key_id)
            if EnrichmentJobStatus.CANCELLED not in ENRICHMENT_TRANSITIONS[job.status]:
                raise ApiError(409, "job_terminal", "The enrichment job is already terminal.")
            self._delete_results(job_id)
            self.connection.execute("UPDATE enrichment_jobs SET status='cancelled', results_json='[]', updated_at=? WHERE enrichment_job_id=? AND status IN ('queued','processing')", (self.clock().isoformat(), job_id))
            return self._row(self.connection.execute("SELECT * FROM enrichment_jobs WHERE enrichment_job_id=?", (job_id,)).fetchone())

    def results(self, job_id, owner_key_id, page, page_size):
        if page < 1 or not 1 <= page_size <= 100:
            raise ApiError(422, "invalid_page", "The page is not valid.")
        with self.lock:
            job = self.get(job_id, owner_key_id)
            if job.status == EnrichmentJobStatus.PROCESSING:
                return [], 0
            if job.status != EnrichmentJobStatus.COMPLETED:
                raise ApiError(409, "result_not_ready", "The enrichment result is not available yet.")
            row = self.connection.execute("SELECT results_json FROM enrichment_jobs WHERE enrichment_job_id=?", (job_id,)).fetchone()
            values = normalize_results(json.loads(row['results_json']))
            return values[(page-1)*page_size:page*page_size], len(values)

    def result_by_detection(self, job_id, owner_key_id, detection_id):
        from app.domain.schemas import EnrichedVehicleResult
        with self.lock:
            job=self.get(job_id,owner_key_id)
            if job.status.value!="completed":
                raise ApiError(409,"preview_source_not_ready","Image results are not ready.")
            row=self.connection.execute("SELECT results_json FROM enrichment_jobs WHERE enrichment_job_id=?",(job_id,)).fetchone()
            matches=[item for item in normalize_results(json.loads(row["results_json"])) if item["detection_id"]==detection_id]
            if len(matches)!=1:raise ApiError(404,"detection_not_found","No accessible detection was found.")
            return EnrichedVehicleResult.model_validate(matches[0])

    def recover(self):
        with self.lock, self.connection:
            now = self.clock().isoformat()
            self.connection.execute("UPDATE enrichment_jobs SET status='queued', updated_at=? WHERE status='processing' AND expires_at>?", (now, now))
            self.cleanup()

    def _delete_results(self, job_id):
        for table in ('enrichment_attributes','enrichment_plates','enrichment_plate_candidates'):
            self.connection.execute(f"DELETE FROM {table} WHERE unit_id IN (SELECT unit_id FROM enrichment_units WHERE enrichment_job_id=?)", (job_id,))
        self.connection.execute("DELETE FROM enrichment_units WHERE enrichment_job_id=?", (job_id,))

    def cleanup(self):
        with self.lock, self.connection:
            now = self.clock().isoformat()
            expired = self.connection.execute("SELECT enrichment_job_id, owner_key_id FROM enrichment_jobs WHERE expires_at<=?", (now,)).fetchall()
            for row in expired:
                self.connection.execute("INSERT OR REPLACE INTO expired_enrichment_jobs VALUES (?,?,?)", (row['enrichment_job_id'],row['owner_key_id'],now))
                self._delete_results(row['enrichment_job_id'])
            self.connection.execute("DELETE FROM enrichment_jobs WHERE expires_at<=?", (now,))

    def close(self):
        with self.lock:
            self.connection.close()

    def _persist_results(self, job_id: str, results: list[dict]) -> None:
        self.connection.execute("DELETE FROM enrichment_units WHERE enrichment_job_id=?", (job_id,))
        for item in results:
            unit_id = f"{job_id}:{item['vehicle_key']}"
            self.connection.execute("INSERT INTO enrichment_units VALUES (?,?,?,?,?,?,?)", (unit_id, job_id, item['detection_id'], item['track_id'], item['class_id'], item['class_name'], json.dumps(item['evidence_frame_indexes'])))
            for attribute in item['attributes']:
                confidence = float(attribute['confidence'])
                if not 0 <= confidence <= 1: raise ValueError("invalid_attribute_confidence")
                self.connection.execute("INSERT INTO enrichment_attributes VALUES (?,?,?,?,?,?)", (unit_id, attribute['name'], attribute['label'], confidence, attribute.get('evidence_frame_index'), "external"))
            plate = item['plate']; text = plate.get('text') if plate.get('status') == 'read' else None
            self.connection.execute("INSERT INTO enrichment_plates VALUES (?,?,?,?,?,?,?)", (unit_id, plate['status'], text, plate.get('localizer_confidence'), plate.get('ocr_confidence'), int(plate.get('used_enhancement', False)), json.dumps(plate.get('evidence_frame_indexes', []))))
    @staticmethod
    def _row(row: sqlite3.Row) -> EnrichmentJob:
        return EnrichmentJob(row['enrichment_job_id'], row['source_kind'], row['source_id'], row['owner_key_id'], EnrichmentJobStatus(row['status']), row['total_units'], row['processed_units'], datetime.fromisoformat(row['created_at']), datetime.fromisoformat(row['updated_at']), datetime.fromisoformat(row['expires_at']), row['error_code'])
