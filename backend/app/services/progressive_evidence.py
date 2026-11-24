"""Bounded original crops and stable per-track identity; no decoding on reads."""

from __future__ import annotations
import json
from pathlib import Path
from uuid import uuid4
import cv2
from app.api.error_handlers import ApiError
from app.services.video_progressive_store import dump


class ProgressiveEvidence:
    def __init__(self, store, root, classes, maximum):
        self.store, self.root, self.classes, self.maximum = store, Path(root), set(classes), maximum
        self.pending = {}
        self.rankings = {}
        self.root.mkdir(parents=True, exist_ok=True)

    def prepare(self, job, frame, pairs):
        result = []
        for d, tid in pairs:
            if d.class_name.lower() not in self.classes:
                continue
            key = (job.job_id, tid)
            if key not in self.rankings:
                with self.store.lock:
                    self.rankings[key] = [
                        dict(r)
                        for r in self.store.db.execute(
                            "SELECT confidence,idx FROM p_evidence WHERE job=? AND track=? AND candidate=1 ORDER BY confidence DESC,idx LIMIT ?",
                            (*key, self.maximum),
                        )
                    ]
            old = self.rankings[key]
            pending = self.pending.get(key, [])
            candidates = old + pending
            rank = lambda x: (-x["confidence"], x.get("idx", 0))
            probe = dict(confidence=d.confidence, idx=frame.frame_index)
            best = sorted(candidates + [probe], key=rank)[: self.maximum]
            if candidates and probe not in best:
                continue
            h, w = frame.image.shape[:2]
            x1, y1, x2, y2 = max(0, d.x_min), max(0, d.y_min), min(w, d.x_max), min(h, d.y_max)
            if x2 <= x1 or y2 <= y1:
                continue
            eid = str(uuid4())
            path = self.root / (eid + ".png")
            ok, png = cv2.imencode(".png", frame.image[y1:y2, x1:x2])
            if not ok:
                continue
            path.write_bytes(png.tobytes())
            item = dict(
                id=eid,
                job=job.job_id,
                track=tid,
                idx=frame.frame_index,
                confidence=d.confidence,
                path=str(path),
                provisional=not candidates,
                meta=dict(
                    frame_index=frame.frame_index,
                    time_us=frame.start_us,
                    vehicle_bbox=dict(x_min=x1, y_min=y1, x_max=x2, y_max=y2),
                    class_id=d.class_id,
                    class_name=d.class_name,
                ),
            )
            pending.append(item)
            self.pending[key] = pending
            result.append(item)
        return result

    def _initial(self, row, job, tid, ordinal, ob, time):
        return dict(
            job_id=job,
            generation=row["generation"],
            unit_id=str(uuid4()),
            track_id=tid,
            discovery_ordinal=ordinal,
            class_name=ob["class_name"],
            first_seen_us=time,
            last_seen_us=time,
            state=("not_requested" if row["on_demand"] else "waiting_evidence")
            if ob["class_name"].lower() in self.classes
            else "not_applicable",
            final=False,
            result_revision=0,
            evidence_revision=0,
            attributes=dict(status="pending", items=[], error_code=None),
            plate=dict(
                status="pending",
                text=None,
                ocr_confidence=None,
                used_enhancement=False,
                policy_id="video-legacy-v1",
                evidence_ids=[],
                error_code=None,
            ),
            evidence=[],
            expires_at=row["expires"],
        )

    def _version(self, job, tid, unit):
        self.store.db.execute(
            "UPDATE p_video SET enrichment_revision=enrichment_revision+1 WHERE job=?", (job,)
        )
        rev = self.store.db.execute(
            "SELECT enrichment_revision FROM p_video WHERE job=?", (job,)
        ).fetchone()[0]
        self.store.db.execute(
            "UPDATE p_tracks SET payload=?,revision=? WHERE job=? AND track=?",
            (dump(unit), rev, job, tid),
        )
        self.store.db.execute(
            "INSERT INTO p_track_versions VALUES(?,?,?,?)", (job, tid, rev, dump(unit))
        )

    def commit(self, job, prepared, frames):
        # Called within publish's transaction, not a nested Connection context.
        row = self.store.row(job.job_id)
        sightings = {}
        for frame in frames:
            if not frame.get("detection_performed", True):
                continue
            for ob in frame["observations"]:
                tid = ob["track_id"]
                if tid not in sightings:
                    sightings[tid] = [ob, frame["start_us"], frame["start_us"]]
                sightings[tid][2] = frame["start_us"]
        ordinal = self.store.db.execute(
            "SELECT count(*) FROM p_tracks WHERE job=?", (job.job_id,)
        ).fetchone()[0]
        for tid, (ob, first, last) in sightings.items():
            rec = self.store.db.execute(
                "SELECT payload FROM p_tracks WHERE job=? AND track=?", (job.job_id, tid)
            ).fetchone()
            if rec:
                unit = json.loads(rec[0])
                unit["last_seen_us"] = last
                self.store.db.execute(
                    "UPDATE p_tracks SET payload=? WHERE job=? AND track=?",
                    (dump(unit), job.job_id, tid),
                )
            else:
                ordinal += 1
                unit = self._initial(row, job.job_id, tid, ordinal, ob, first)
                unit["last_seen_us"] = last
                self.store.db.execute(
                    "INSERT INTO p_tracks VALUES(?,?,?,?,0)", (job.job_id, tid, ordinal, dump(unit))
                )
            self._version(job.job_id, tid, unit)
        touched = set()
        for item in prepared:
            self.store.db.execute(
                "INSERT OR IGNORE INTO p_evidence(id,job,track,idx,confidence,path,payload,provisional) VALUES(?,?,?,?,?,?,?,?)",
                (
                    item["id"],
                    item["job"],
                    item["track"],
                    item["idx"],
                    item["confidence"],
                    item["path"],
                    dump(item["meta"]),
                    int(item["provisional"]),
                ),
            )
            touched.add(item["track"])
        for tid in touched:
            ranked = self.store.db.execute(
                "SELECT id,path,result,provisional,confidence,idx FROM p_evidence WHERE job=? AND track=? ORDER BY confidence DESC,idx LIMIT ?",
                (job.job_id, tid, self.maximum),
            ).fetchall()
            self.rankings[(job.job_id, tid)] = [
                dict(confidence=r["confidence"], idx=r["idx"]) for r in ranked
            ]
            ids = [r["id"] for r in ranked]
            self.store.db.execute(
                "UPDATE p_evidence SET candidate=0 WHERE job=? AND track=?", (job.job_id, tid)
            )
            if ids:
                self.store.db.execute(
                    "UPDATE p_evidence SET candidate=1 WHERE id IN ("
                    + ",".join("?" * len(ids))
                    + ")",
                    ids,
                )
            for loser in self.store.db.execute(
                "SELECT id,path FROM p_evidence WHERE job=? AND track=? AND candidate=0 AND provisional=0 AND requested=0 AND result IS NULL AND claimed=0",
                (job.job_id, tid),
            ).fetchall():
                Path(loser["path"]).unlink(missing_ok=True)
                self.store.db.execute("DELETE FROM p_evidence WHERE id=?", (loser["id"],))
            self.pending.pop((job.job_id, tid), None)

    def initialize(self):
        with self.store.lock, self.store.db:
            self.store.db.execute(
                "CREATE TABLE IF NOT EXISTS p_track_versions(job TEXT,track INTEGER,revision INTEGER,payload TEXT,PRIMARY KEY(job,track,revision))"
            )

    def request(self, job, owner, tid):
        """An explicit request freezes current top-K; repeat selection is idempotent."""
        with self.store.lock, self.store.db:
            row = self.store.row(job, owner)
            unit = self.track(job, owner, tid)
            if not row["on_demand"]:
                return unit
            if self.store.db.execute("SELECT 1 FROM p_enrichment_requests WHERE job=? AND track=?", (job, tid)).fetchone():
                return unit
            unit = self.track(job,owner,tid)
            if unit["state"] == "not_applicable":
                unit.update(final=True)
                unit["attributes"]["status"] = unit["plate"]["status"] = "not_applicable"
                self._version(job,tid,unit)
                return unit
            records = self.store.db.execute("SELECT * FROM p_evidence WHERE job=? AND track=? AND candidate=1 ORDER BY confidence DESC,idx LIMIT ?", (job, tid, self.maximum)).fetchall()
            if not records:
                raise ApiError(409, "evidence_not_ready", "The evidence is not ready.")
            self.store.db.execute("INSERT INTO p_enrichment_requests VALUES(?,?)", (job,tid))
            self.store.db.executemany("UPDATE p_evidence SET requested=1 WHERE id=?", [(r["id"],) for r in records])
            unit.update(state="queued", final=False)
            unit["evidence"] = []
            for rec in records:
                meta=json.loads(rec["payload"])
                base=f"/api/v1/video-jobs/{job}/playback/tracks/{tid}/evidence/{rec['id']}"
                unit["evidence"].append(dict(evidence_id=rec["id"],frame_index=rec["idx"],time_us=meta["time_us"],vehicle_bbox=meta["vehicle_bbox"],provisional=True,vehicle_url=base+"/vehicle",plate_url=None,expires_at=row["expires"]))
            unit["evidence_revision"] += 1
            unit["result_revision"] += 1
            self._version(job, tid, unit)
            return unit

    def track(self, job, owner, tid):
        with self.store.lock:
            self.store.row(job, owner)
            rec = self.store.db.execute(
                "SELECT payload FROM p_tracks WHERE job=? AND track=?", (job, tid)
            ).fetchone()
            if rec is None:
                raise ApiError(404, "track_not_found", "The vehicle is unavailable.")
            return json.loads(rec[0])

    def tracks(self, job, owner, snapshot, cursor=None):
        with self.store.lock:
            row = self.store.row(job, owner)
            if snapshot > row["enrichment_revision"]:
                raise ApiError(409, "snapshot_stale", "Refresh the snapshot.")
            context = (
                __import__("hashlib")
                .sha256(dump([job, owner, row["generation"], "tracks", snapshot]).encode())
                .hexdigest()
            )
            after, _ = self.store._position(cursor, context, 0)
            result = []
            for rec in self.store.db.execute(
                """SELECT v.payload FROM p_track_versions v
                JOIN (SELECT track,MAX(revision) r FROM p_track_versions WHERE job=? AND revision<=? GROUP BY track) x
                ON v.track=x.track AND v.revision=x.r WHERE v.job=?""",
                (job, snapshot, job),
            ):
                unit = json.loads(rec[0])
                if unit["discovery_ordinal"] > after:
                    result.append(unit)
            result.sort(key=lambda u: u["discovery_ordinal"])
            page = []
            size = 0
            for unit in result[:100]:
                length = len(dump(unit))
                if page and size + length > 1_000_000:
                    break
                page.append(unit)
                size += length
            more = len(result) > len(page)
            token = self.store._cursor(context, page[-1]["discovery_ordinal"], 0) if more else None
            return dict(
                job_id=job,
                generation=row["generation"],
                snapshot=snapshot,
                items=page,
                next_cursor=token,
            )

    def resource(self, job, owner, tid, eid, kind):
        with self.store.lock:
            self.store.row(job, owner)
            rec = self.store.db.execute(
                "SELECT path,result FROM p_evidence WHERE job=? AND track=? AND id=?",
                (job, tid, eid),
            ).fetchone()
            if rec is None:
                raise ApiError(404, "evidence_not_found", "The evidence is unavailable.")
            path = Path(rec["path"])
            if kind == "plate":
                path = path.with_suffix(".plate.png")
            if not path.is_file():
                raise ApiError(404, "evidence_not_found", "The evidence is unavailable.")
            return path

    def discard_pending(self, job):
        for key in [k for k in self.rankings if k[0] == job]:
            self.rankings.pop(key, None)
        for key in [k for k in self.pending if k[0] == job]:
            for item in self.pending.pop(key, []):
                with self.store.lock:
                    known = self.store.db.execute(
                        "SELECT 1 FROM p_evidence WHERE id=?", (item["id"],)
                    ).fetchone()
                if not known:
                    Path(item["path"]).unlink(missing_ok=True)

    def cleanup(self):
        # A crash can leave closed PNGs which never acquired a durable receipt.
        import re, time

        with self.store.lock:
            protected = {r[0] for r in self.store.db.execute("SELECT path FROM p_evidence")}
            protected |= {str(Path(p).with_suffix(".plate.png")) for p in list(protected)}
            protected |= {
                item["path"] for values in list(self.pending.values()) for item in list(values)
            }
        for path in self.root.glob("*.png"):
            if not re.fullmatch(r"[a-f0-9-]{36}(?:\.plate)?\.png", path.name):
                continue
            if str(path) not in protected:
                try:
                    if time.time() - path.stat().st_mtime > 60:
                        path.unlink(missing_ok=True)
                except OSError:
                    pass
