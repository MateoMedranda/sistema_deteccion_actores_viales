"""Optional line counts over persisted source-PTS observations. No decode or inference."""
import json
from app.api.error_handlers import ApiError
from app.domain.models import CountPoint
from app.services.line_counting import validate_line, side_of_line, direction
from app.services.video_progressive_store import dump

class ProgressiveCountService:
    def __init__(self, store):
        self.store = store
        with store.lock, store.db:
            store.db.execute("CREATE TABLE IF NOT EXISTS p_count_state(job TEXT PRIMARY KEY,line TEXT,processed INTEGER NOT NULL DEFAULT 0,sides TEXT NOT NULL DEFAULT '{}',revision INTEGER NOT NULL DEFAULT 1)")
            store.db.execute("CREATE TABLE IF NOT EXISTS p_count_events(job TEXT,track INTEGER,time_us INTEGER,direction TEXT,PRIMARY KEY(job,track))")
            store.db.execute("CREATE INDEX IF NOT EXISTS p_count_time ON p_count_events(job,time_us)")

    def configure(self, job, owner, points):
        line = validate_line(CountPoint(**points["point_a"]), CountPoint(**points["point_b"]))
        canonical = dump(dict(point_a=vars(line.point_a),point_b=vars(line.point_b)))
        with self.store.lock, self.store.db:
            self.store.row(job, owner)
            old = self.store.db.execute("SELECT * FROM p_count_state WHERE job=?",(job,)).fetchone()
            if old is None or old["line"] != canonical:
                revision = old["revision"] + 1 if old else 1
                self.store.db.execute("DELETE FROM p_count_events WHERE job=?",(job,))
                self.store.db.execute("INSERT OR REPLACE INTO p_count_state VALUES(?,?,0,'{}',?)",(job,canonical,revision))
            return self.snapshot(job,owner)

    def disable(self, job, owner):
        with self.store.lock, self.store.db:
            self.store.row(job,owner)
            self.store.db.execute("DELETE FROM p_count_events WHERE job=?",(job,))
            self.store.db.execute("UPDATE p_count_state SET line=NULL,processed=0,sides='{}',revision=revision+1 WHERE job=?",(job,))

    def snapshot(self, job, owner, at_us=None):
        with self.store.lock, self.store.db:
            source = self.store.row(job,owner)
            if at_us is None:at_us=source["last_start"] or 0
            if at_us < 0 or at_us > source["until_us"]:
                raise ApiError(409,"interval_not_ready","The interval is not available.")
            state = self.store.db.execute("SELECT * FROM p_count_state WHERE job=?",(job,)).fetchone()
            enabled = state is not None and state["line"] is not None
            a=b=0
            if enabled:
                data=json.loads(state["line"])
                line=validate_line(CountPoint(**data["point_a"]),CountPoint(**data["point_b"]))
                sizes=json.loads(source["timeline"])
                sides=json.loads(state["sides"])
                counted={r[0] for r in self.store.db.execute("SELECT track FROM p_count_events WHERE job=?",(job,))}
                processed=state["processed"]
                for rec in self.store.db.execute("SELECT idx,payload FROM p_frames WHERE job=? AND idx>=? ORDER BY idx",(job,processed)):
                    frame=json.loads(rec["payload"])
                    # Estimates are for display; only measurements confirm a crossing.
                    for ob in (frame["observations"] if frame.get("detection_performed", True) else []):
                        box=ob["raw_bbox"];tid=ob["track_id"];key=str(tid)
                        point=CountPoint((box["x_min"]+box["x_max"])/(2*sizes["width"]),(box["y_min"]+box["y_max"])/(2*sizes["height"]))
                        side=side_of_line(point,line)
                        if side == 0:continue
                        crossed=direction(sides.get(key,0),side)
                        if crossed and tid not in counted:
                            self.store.db.execute("INSERT OR IGNORE INTO p_count_events VALUES(?,?,?,?)",(job,tid,frame["start_us"],crossed));counted.add(tid)
                        sides[key]=side
                    processed=rec["idx"]+1
                self.store.db.execute("UPDATE p_count_state SET processed=?,sides=? WHERE job=?",(processed,dump(sides),job))
                for rec in self.store.db.execute("SELECT direction,COUNT(*) n FROM p_count_events WHERE job=? AND time_us<=? GROUP BY direction",(job,at_us)):
                    if rec["direction"]=="A_to_B":a=rec["n"]
                    else:b=rec["n"]
            return dict(job_id=job,generation=source["generation"],enabled=enabled,line=json.loads(state["line"]) if enabled else None,revision=state["revision"] if state else 0,at_us=at_us,available_until_us=source["until_us"],total=a+b,a_to_b=a,b_to_a=b)
