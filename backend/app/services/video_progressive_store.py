"""Durable confirmed prefix. Files/observations are never exposed before commit."""

from __future__ import annotations
import base64, hashlib, hmac, json, secrets, sqlite3, threading
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4
from app.api.error_handlers import ApiError


def dump(value):
    return json.dumps(value, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def now():
    return datetime.now(UTC)


class ProgressiveStore:
    def __init__(self, path: Path, legacy=None, buffer_seconds=5):
        self.legacy = legacy
        self.lock = legacy._lock if legacy else threading.RLock()
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = legacy._connection if legacy else sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.secret = secrets.token_bytes(32)
        self.buffer_seconds = buffer_seconds
        self.readers = {}
        with self.lock, self.db:
            self.db.executescript("""
            CREATE TABLE IF NOT EXISTS p_video(
              job TEXT PRIMARY KEY,owner TEXT NOT NULL,generation TEXT NOT NULL,revision INTEGER NOT NULL DEFAULT 0,
              analysis TEXT NOT NULL DEFAULT 'queued',export TEXT NOT NULL DEFAULT 'waiting',
              frames INTEGER NOT NULL DEFAULT 0,until_us INTEGER NOT NULL DEFAULT 0,last_start INTEGER,
              timeline TEXT NOT NULL,source TEXT NOT NULL,expires TEXT NOT NULL,retired INTEGER NOT NULL DEFAULT 0,
              error TEXT,closed INTEGER NOT NULL DEFAULT 0,enrichment_revision INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS p_frames(
              job TEXT NOT NULL,idx INTEGER NOT NULL,start INTEGER NOT NULL,end INTEGER NOT NULL,
              revision INTEGER NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(job,idx));
            CREATE INDEX IF NOT EXISTS p_frame_time ON p_frames(job,start,end);
            CREATE TABLE IF NOT EXISTS p_tracks(
              job TEXT NOT NULL,track INTEGER NOT NULL,ordinal INTEGER NOT NULL,payload TEXT NOT NULL,
              revision INTEGER NOT NULL DEFAULT 0,PRIMARY KEY(job,track));
            CREATE TABLE IF NOT EXISTS p_evidence(
              id TEXT PRIMARY KEY,job TEXT NOT NULL,track INTEGER NOT NULL,idx INTEGER NOT NULL,
              confidence REAL NOT NULL,path TEXT NOT NULL,payload TEXT NOT NULL,
              candidate INTEGER NOT NULL DEFAULT 1,provisional INTEGER NOT NULL DEFAULT 0,
              result TEXT,claimed INTEGER NOT NULL DEFAULT 0);
            CREATE INDEX IF NOT EXISTS p_evidence_track ON p_evidence(job,track,confidence DESC,idx);
            CREATE INDEX IF NOT EXISTS p_evidence_queue ON p_evidence(claimed,job,idx);
            """)
            self.db.execute(
                "UPDATE p_video SET analysis='partial_failed',closed=1,error='processing_interrupted' WHERE analysis='analyzing'"
            )
            self.db.execute("UPDATE p_evidence SET claimed=0 WHERE claimed=1 AND result IS NULL")

    def create(self, job, owner, source, metadata, expires):
        timeline = dict(
            timebase="source-pts",
            width=metadata["width"],
            height=metadata["height"],
            display_width=metadata["width"],
            display_height=metadata["height"],
            pixel_to_display=[1, 0, 0, 1, 0, 0],
            duration_us=round(metadata["duration"] * 1e6),
            duration_confirmed=False,
            pts_origin="0",
            time_base_num=1,
            time_base_den=1,
            playback_offset_us=0,
        )
        with self.lock, self.db:
            self.db.execute(
                "INSERT OR IGNORE INTO p_video(job,owner,generation,timeline,source,expires) VALUES(?,?,?,?,?,?)",
                (job, owner, str(uuid4()), dump(timeline), str(source), expires.isoformat()),
            )
        return self.snapshot(job, owner)

    def exists(self, job):
        with self.lock:
            return (
                self.db.execute("SELECT 1 FROM p_video WHERE job=?", (job,)).fetchone() is not None
            )

    def row(self, job, owner=None):
        with self.lock:
            row = self.db.execute("SELECT * FROM p_video WHERE job=?", (job,)).fetchone()
            if row is None or (owner is not None and owner != row["owner"]):
                raise ApiError(404, "artifact_not_found", "The requested resource is unavailable.")
            if row["retired"] or datetime.fromisoformat(row["expires"]) <= now():
                raise ApiError(410, "artifact_expired", "The requested resource is unavailable.")
            return row

    def set_timeline(self, job, timeline):
        with self.lock, self.db:
            row = self.row(job)
            if timeline.get("duration_us") is None:
                timeline = {**timeline, "duration_us": json.loads(row["timeline"])["duration_us"]}
            self.db.execute(
                "UPDATE p_video SET timeline=?,analysis='analyzing' WHERE job=?",
                (dump(timeline), job),
            )

    def publish(self, job, frames, on_publish=None):
        if not frames:
            return
        with self.lock, self.db:
            row = self.row(job)
            if row["closed"]:
                raise ApiError(409, "source_closed", "The analysis is terminal.")
            timeline = json.loads(row["timeline"])
            expected, count = row["until_us"], row["frames"]
            revision = row["revision"] + 1
            for frame in frames:
                old = self.db.execute(
                    "SELECT payload FROM p_frames WHERE job=? AND idx=?",
                    (job, frame["frame_index"]),
                ).fetchone()
                if old:
                    if old["payload"] != dump(
                        {
                            **frame,
                            "observations": [
                                {**ob, "ordinal": i} for i, ob in enumerate(frame["observations"])
                            ],
                        }
                    ):
                        raise ValueError("conflicting_batch")
                    continue
                if (
                    frame["frame_index"] != count
                    or frame["start_us"] != expected
                    or frame["end_us"] <= expected
                ):
                    raise ValueError("non_contiguous_batch")
                for ordinal, ob in enumerate(frame["observations"]):
                    b = ob["raw_bbox"]
                    if (
                        ob["track_id"] <= 0
                        or not 0 <= ob["confidence"] <= 1
                        or not (
                            0 <= b["x_min"] < b["x_max"]
                            and 0 <= b["y_min"] < b["y_max"]
                            and b["x_max"] <= timeline["width"]
                            and b["y_max"] <= timeline["height"]
                        )
                    ):
                        raise ValueError("invalid_observation")
                    ob["ordinal"] = ordinal
                self.db.execute(
                    "INSERT INTO p_frames VALUES(?,?,?,?,?,?)",
                    (job, count, expected, frame["end_us"], revision, dump(frame)),
                )
                if self.legacy:
                    self.db.executemany(
                        "INSERT OR REPLACE INTO video_detections VALUES(?,?,?,?,?,?,?,?,?,?)",
                        [
                            (
                                job,
                                count,
                                o["track_id"],
                                o["class_id"],
                                o["class_name"],
                                o["confidence"],
                                o["raw_bbox"]["x_min"],
                                o["raw_bbox"]["y_min"],
                                o["raw_bbox"]["x_max"],
                                o["raw_bbox"]["y_max"],
                            )
                            for o in frame["observations"]
                        ],
                    )
                expected = frame["end_us"]
                count += 1
            if count != row["frames"]:
                self.row(job)  # expiry may race a large batch
                self.db.execute(
                    "UPDATE p_video SET revision=?,frames=?,until_us=?,last_start=?,analysis='analyzing' WHERE job=?",
                    (revision, count, expected, frames[-1]["start_us"], job),
                )
                if on_publish:
                    on_publish()

    def finish_analysis(self, job, error=None):
        with self.lock, self.db:
            row = self.row(job)
            timeline = json.loads(row["timeline"])
            if not error:
                timeline.update(duration_us=row["until_us"], duration_confirmed=True)
            self.db.execute(
                "UPDATE p_video SET analysis=?,closed=1,error=?,timeline=?,revision=revision+1 WHERE job=?",
                ("partial_failed" if error else "complete", error, dump(timeline), job),
            )

    def export(self, job, status):
        with self.lock, self.db:
            self.row(job)
            self.db.execute("UPDATE p_video SET export=? WHERE job=?", (status, job))

    def summary(self, row):
        units = [
            json.loads(x[0])
            for x in self.db.execute("SELECT payload FROM p_tracks WHERE job=?", (row["job"],))
        ]
        terminal = sum(u["final"] for u in units)
        ready = sum(u["state"] in ("ready", "partial") for u in units)
        closed = bool(row["closed"])
        status = (
            "discovering"
            if not closed
            else "processing"
            if terminal < len(units)
            else "not_applicable"
            if not units
            else "partial"
            if any(u["state"] in ("failed", "partial") for u in units)
            else "complete"
        )
        return dict(
            revision=row["enrichment_revision"],
            status=status,
            source_closed=closed,
            discovered_units=len(units),
            provisional_ready_units=ready,
            terminal_units=terminal,
            total_units=len(units) if closed else None,
        )

    def snapshot(self, job, owner):
        with self.lock:
            row = self.row(job, owner)
            available = row["frames"] > 0 and Path(row["source"]).is_file()
            # Unit tests can publish before materializing media; prefix remains a factual analysis value.
            return dict(
                job_id=job,
                generation=row["generation"],
                revision=row["revision"],
                analysis_state=row["analysis"],
                export_state=row["export"],
                frames_processed=row["frames"],
                frames_published=row["frames"],
                available_until_us=row["until_us"],
                last_frame_start_us=row["last_start"],
                media_available=available,
                source=dict(
                    url=f"/api/v1/video-jobs/{job}/playback/source",
                    media_type="video/mp4",
                    size_bytes=Path(row["source"]).stat().st_size,
                )
                if available
                else None,
                timeline=json.loads(row["timeline"]),
                buffer_seconds=self.buffer_seconds,
                expires_at=row["expires"],
                error_code=row["error"],
                enrichment=self.summary(row),
            )

    def _cursor(self, context, index, offset):
        payload = (
            base64.urlsafe_b64encode(dump([context, index, offset]).encode()).decode().rstrip("=")
        )
        sig = hmac.new(self.secret, payload.encode(), hashlib.sha256).hexdigest()
        return payload + "_" + sig

    def _position(self, token, context, start):
        if token is None:
            return start, 0
        try:
            payload, sig = token.rsplit("_", 1)
            if not hmac.compare_digest(
                sig, hmac.new(self.secret, payload.encode(), hashlib.sha256).hexdigest()
            ):
                raise ValueError()
            ctx, index, offset = json.loads(
                base64.urlsafe_b64decode(payload + "=" * ((-len(payload)) % 4))
            )
            if (
                ctx != context
                or not isinstance(index, int)
                or not isinstance(offset, int)
                or min(index, offset) < 0
            ):
                raise ValueError()
            return index, offset
        except Exception:
            raise ApiError(409, "cursor_context_mismatch", "The cursor is no longer usable.")

    def frames(self, job, owner, start, end, snapshot, cursor=None):
        if start < 0 or end <= start or end - start > 30_000_000:
            raise ApiError(422, "window_invalid", "Invalid window.")
        with self.lock:
            row = self.row(job, owner)
            bound = (
                self.db.execute(
                    "SELECT MAX(end) FROM p_frames WHERE job=? AND revision<=?", (job, snapshot)
                ).fetchone()[0]
                or 0
            )
            if snapshot > row["revision"] or end > bound:
                raise ApiError(409, "interval_not_ready", "The interval is not available.")
            context = hashlib.sha256(
                dump([job, owner, row["generation"], start, end, snapshot]).encode()
            ).hexdigest()
            first = self.db.execute(
                "SELECT MIN(idx) FROM p_frames WHERE job=? AND end>? AND start<?", (job, start, end)
            ).fetchone()[0]
            index, offset = self._position(cursor, context, first or 0)
            out = []
            total = 0
            size = 0
            continuation = None
            for rec in self.db.execute(
                "SELECT payload FROM p_frames WHERE job=? AND idx>=? AND start<? AND end>? AND revision<=? ORDER BY idx",
                (job, index, end, start, snapshot),
            ):
                frame = json.loads(rec[0])
                obs = frame["observations"]
                pos = offset if frame["frame_index"] == index else 0
                while True:
                    if total >= 1000 and pos < len(obs):
                        continuation = self._cursor(context, frame["frame_index"], pos)
                        break
                    part = obs[pos : pos + min(250, 1000 - total)]
                    entry = {k: frame[k] for k in ("frame_index", "start_us", "end_us", "pts")}
                    entry.update(
                        observation_offset=pos, observation_total=len(obs), observations=part
                    )
                    length = len(dump(entry))
                    if out and (
                        total + len(part) > 1000 or size + length > 1_000_000 or len(out) >= 100
                    ):
                        continuation = self._cursor(context, frame["frame_index"], pos)
                        break
                    out.append(entry)
                    size += length
                    total += len(part)
                    pos += len(part)
                    if pos >= len(obs):
                        break
                    if total >= 1000:
                        continuation = self._cursor(context, frame["frame_index"], pos)
                        break
                if continuation:
                    break
                offset = 0
            return dict(
                job_id=job,
                generation=row["generation"],
                snapshot=snapshot,
                from_us=start,
                to_us=end,
                frames=out,
                next_cursor=continuation,
            )

    def withdraw(self, job, owner):
        with self.lock, self.db:
            rec = self.db.execute("SELECT owner FROM p_video WHERE job=?", (job,)).fetchone()
            if rec is None or rec[0] != owner:
                raise ApiError(404, "artifact_not_found", "Unavailable.")
            self.db.execute("UPDATE p_video SET retired=1,closed=1 WHERE job=?", (job,))
            if self.legacy:
                self.db.execute(
                    "UPDATE video_jobs SET status='cancelled',processing_phase='cancelled' WHERE job_id=? AND status IN ('queued','processing')",
                    (job,),
                )
        self.cleanup()

    def retained(self, path):
        with self.lock:
            if self.readers.get(str(path)):
                return True
            if self.db.execute(
                "SELECT 1 FROM p_video WHERE source=? AND retired=0 AND expires>?",
                (str(path), now().isoformat()),
            ).fetchone():
                return True
            if self.legacy:
                return (
                    self.db.execute(
                        "SELECT 1 FROM video_jobs j JOIN p_video p ON p.job=j.job_id WHERE j.output_path=? AND p.retired=0 AND p.expires>?",
                        (str(path), now().isoformat()),
                    ).fetchone()
                    is not None
                )
            return False

    def cleanup(self):
        with self.lock, self.db:
            rows = self.db.execute(
                "SELECT * FROM p_video WHERE retired=1 OR expires<=?", (now().isoformat(),)
            ).fetchall()
            for row in rows:
                paths = [Path(row["source"])] if row["source"] else []
                paths += [
                    Path(x[0])
                    for x in self.db.execute(
                        "SELECT path FROM p_evidence WHERE job=?", (row["job"],)
                    )
                ]
                paths += [p.with_suffix(".plate.png") for p in paths[1:]]
                if self.legacy:
                    parent = self.db.execute(
                        "SELECT output_path FROM video_jobs WHERE job_id=?", (row["job"],)
                    ).fetchone()
                    if parent and parent[0]:
                        paths.append(Path(parent[0]))
                if any(self.readers.get(str(p)) for p in paths):
                    continue
                for path in paths:
                    if not self.readers.get(str(path)):
                        try:
                            path.unlink(missing_ok=True)
                        except OSError:
                            pass
                self.db.execute("DELETE FROM p_frames WHERE job=?", (row["job"],))
                self.db.execute("DELETE FROM p_tracks WHERE job=?", (row["job"],))
                self.db.execute("DELETE FROM p_evidence WHERE job=?", (row["job"],))
                if self.db.execute(
                    "SELECT 1 FROM sqlite_master WHERE name='p_track_versions'"
                ).fetchone():
                    self.db.execute("DELETE FROM p_track_versions WHERE job=?", (row["job"],))

    def close(self):
        if not self.legacy:
            with self.lock:
                self.db.close()
