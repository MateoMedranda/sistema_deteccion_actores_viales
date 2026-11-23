"""One bounded worker using already-loaded enrichment adapters."""

import json, threading
from pathlib import Path
import cv2
import numpy as np
from app.api.error_handlers import ApiError
from app.services.plate_consensus import PlateCandidate, consensus
from app.services.video_progressive_store import dump, now


class ProgressiveEnrichment:
    def __init__(self, evidence, processor, logger, slots=None):
        self.evidence = evidence
        self.store = evidence.store
        self.processor = processor
        self.logger = logger
        self.slots = slots or threading.Lock()
        self.dirty = set()
        self.closed_sources = {}
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self.run, name="progressive-enrichment", daemon=True)

    def start(self):
        self.thread.start()

    def close(self):
        self.stop.set()
        self.thread.join()

    def claim(self):
        with self.store.lock, self.store.db:
            rec = self.store.db.execute(
                """SELECT e.* FROM p_evidence e JOIN p_video v ON e.job=v.job
              WHERE v.retired=0 AND v.expires>? AND e.result IS NULL AND e.claimed=0
              AND ((v.on_demand=1 AND e.requested=1) OR (v.on_demand=0 AND ((v.closed=0 AND e.provisional=1) OR (v.closed=1 AND e.candidate=1))))
              ORDER BY e.provisional DESC,e.idx LIMIT 1""",
                (now().isoformat(),),
            ).fetchone()
            if rec:
                self.store.db.execute("UPDATE p_evidence SET claimed=1 WHERE id=?", (rec["id"],))
            return dict(rec) if rec else None

    def run(self):
        while not self.stop.is_set():
            rec = self.claim()
            if rec:
                try:
                    with self.store.lock, self.store.db:
                        unit = self.evidence.track(rec["job"], self.store.row(rec["job"])["owner"], rec["track"])
                        if unit["state"] == "queued":
                            unit["state"] = "processing"
                            self.evidence._version(rec["job"], rec["track"], unit)
                    self.evaluate(rec)
                except ApiError:
                    pass  # Withdrawal/expiry won the race; no result may be revived.
                except Exception:
                    self.logger.error(
                        "progressive_enrichment_failed",
                        extra={"job_id": rec["job"], "error_code": "processing_failed"},
                    )
                    with self.store.lock, self.store.db:
                        self.store.db.execute(
                            "UPDATE p_evidence SET result=?,claimed=0 WHERE id=?",
                            (dump({"error": "processing_failed"}), rec["id"]),
                        )
            else:
                self.stop.wait(0.1)
            if rec:
                self.dirty.add(rec["job"])
            self.refresh()

    def evaluate(self, rec):
        path = Path(rec["path"])
        image = cv2.imdecode(np.frombuffer(path.read_bytes(), np.uint8), cv2.IMREAD_COLOR)

        def active():
            if self.stop.is_set():
                return False
            try:
                with self.store.lock:
                    self.store.row(rec["job"])
                return True
            except Exception:
                return False

        if not active():
            return
        with self.slots:
            if not active():
                return
            attributes, plate = self.processor.enrich(
                image, rec["idx"], job_id=rec["job"], source_type="video", should_continue=active
            )
        if not active():
            return
        plate_bytes = None
        if plate.get("bbox_relative"):
            b = plate["bbox_relative"]
            h, w = image.shape[:2]
            x1, y1, x2, y2 = [
                round(v * s)
                for v, s in zip((b["x_min"], b["y_min"], b["x_max"], b["y_max"]), (w, h, w, h))
            ]
            if x2 > x1 and y2 > y1:
                ok, png = cv2.imencode(".png", image[y1:y2, x1:x2])
                if ok:
                    plate_bytes = png.tobytes()
        with self.store.lock, self.store.db:
            self.store.row(rec["job"])
            if plate_bytes:
                path.with_suffix(".plate.png").write_bytes(plate_bytes)
            self.store.db.execute(
                "UPDATE p_evidence SET result=?,claimed=0 WHERE id=?",
                (dump(dict(attributes=attributes, plate=plate)), rec["id"]),
            )

    def refresh(self):
        with self.store.lock, self.store.db:
            rows = self.store.db.execute(
                "SELECT * FROM p_video WHERE retired=0 AND expires>?", (now().isoformat(),)
            ).fetchall()
            active = {row["job"] for row in rows}
            self.dirty.intersection_update(active)
            self.closed_sources = {
                job: closed for job, closed in self.closed_sources.items() if job in active
            }
            for row in rows:
                if (
                    row["job"] not in self.dirty
                    and self.closed_sources.get(row["job"]) == row["closed"]
                ):
                    continue
                self.closed_sources[row["job"]] = row["closed"]
                self.dirty.discard(row["job"])
                for unitrow in self.store.db.execute(
                    "SELECT * FROM p_tracks WHERE job=?", (row["job"],)
                ).fetchall():
                    unit = json.loads(unitrow["payload"])
                    if row["on_demand"] and not self.store.db.execute("SELECT 1 FROM p_enrichment_requests WHERE job=? AND track=?", (row["job"], unitrow["track"])).fetchone():
                        continue
                    records = [
                        dict(x)
                        for x in self.store.db.execute(
                            "SELECT * FROM p_evidence WHERE job=? AND track=? AND "
                            + ("requested=1" if row["on_demand"] else "candidate=1" if row["closed"] else "provisional=1")
                            + " ORDER BY confidence DESC,idx",
                            (row["job"], unitrow["track"]),
                        )
                    ]
                    complete = (bool(row["closed"]) or bool(row["on_demand"])) and all(x["result"] is not None for x in records)
                    ready = [x for x in records if x["result"]]
                    if not ready and not complete:
                        continue
                    outputs = [(x, json.loads(x["result"])) for x in ready]
                    valid = [(x, y) for x, y in outputs if "attributes" in y]
                    old = dump(unit)
                    unit["final"] = complete
                    unit["evidence"] = []
                    for x, y in valid:
                        meta = json.loads(x["payload"])
                        base = f"/api/v1/video-jobs/{row['job']}/playback/tracks/{unitrow['track']}/evidence/{x['id']}"
                        unit["evidence"].append(
                            dict(
                                evidence_id=x["id"],
                                frame_index=x["idx"],
                                time_us=meta["time_us"],
                                vehicle_bbox=meta["vehicle_bbox"],
                                provisional=not complete,
                                vehicle_url=base + "/vehicle",
                                plate_url=base + "/plate"
                                if Path(x["path"]).with_suffix(".plate.png").is_file()
                                else None,
                                expires_at=row["expires"],
                            )
                        )
                    if valid:
                        unit["class_name"] = json.loads(valid[0][0]["payload"])["class_name"]
                        primary, value = valid[0]
                        attrs = value["attributes"]
                        plate = value["plate"]
                        candidates = [
                            PlateCandidate(
                                y["plate"].get("text") or "",
                                y["plate"].get("ocr_confidence") or 0,
                                y["plate"].get("localizer_confidence") or 0,
                                1.0,
                                x["idx"],
                            )
                            for x, y in valid
                            if y["plate"].get("status") == "read"
                        ]
                        winner = consensus(candidates, self.processor.accept_threshold)
                        if winner:
                            primary, value = next(
                                (x, y) for x, y in valid if x["idx"] == winner.frame_index
                            )
                            plate = value["plate"]
                        elif candidates:
                            plate = {**plate, "status": "unreadable", "text": None}
                        unit["attributes"] = dict(
                            status=attrs["status"],
                            items=[
                                dict(
                                    name=a["name"],
                                    value=a["label"],
                                    confidence=a["confidence"],
                                    evidence_id=valid[0][0]["id"],
                                )
                                for a in attrs["items"]
                            ],
                            error_code=attrs.get("error_code"),
                        )
                        unit["plate"] = dict(
                            status=plate["status"],
                            text=plate.get("text"),
                            ocr_confidence=plate.get("ocr_confidence"),
                            used_enhancement=plate.get("used_enhancement", False),
                            policy_id="video-legacy-v1",
                            evidence_ids=[
                                x["id"]
                                for x, y in valid
                                if not winner or y["plate"].get("text") == winner.text
                            ],
                            error_code=plate.get("error_code"),
                        )
                        unit["state"] = (
                            "ready"
                            if attrs["status"] == "completed" and plate["status"] != "failed"
                            else "partial"
                        )
                    elif complete:
                        unit["state"] = (
                            "not_applicable"
                            if unit["class_name"].lower() not in self.evidence.classes
                            else "failed"
                        )
                        unit["attributes"] = dict(
                            status="not_applicable"
                            if unit["state"] == "not_applicable"
                            else "failed",
                            items=[],
                            error_code=None
                            if unit["state"] == "not_applicable"
                            else "evidence_unavailable",
                        )
                        unit["plate"].update(
                            status="not_applicable"
                            if unit["state"] == "not_applicable"
                            else "failed",
                            error_code=None
                            if unit["state"] == "not_applicable"
                            else "evidence_unavailable",
                        )
                    # Compare without revision counters; unchanged results are not republished.
                    if dump(unit) != old:
                        unit["result_revision"] += 1
                        unit["evidence_revision"] = len(unit["evidence"])
                        self.evidence._version(row["job"], unitrow["track"], unit)
