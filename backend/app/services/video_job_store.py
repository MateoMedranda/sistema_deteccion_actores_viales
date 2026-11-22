from __future__ import annotations
import json,sqlite3,threading
from datetime import UTC,datetime,timedelta
from pathlib import Path
from uuid import uuid4
from app.api.error_handlers import ApiError
from app.domain.models import FrameDetection,VideoJob,VideoJobStatus,VideoMetadata,may_transition

class VideoJobStore:
    def __init__(self,path:Path,ttl_seconds:int,max_queued:int,clock=None):
        self.path,self.ttl,self.max_queued=path,timedelta(seconds=ttl_seconds),max_queued
        self.clock=clock or (lambda:datetime.now(UTC))
        self._lock=threading.RLock();self._purged:set[Path]=set();self._resources:dict[str,set[Path]]={}
        path.parent.mkdir(parents=True,exist_ok=True)
        self._connection=sqlite3.connect(path,check_same_thread=False);self._connection.row_factory=sqlite3.Row
        self._connection.execute("""CREATE TABLE IF NOT EXISTS video_jobs (
          job_id TEXT PRIMARY KEY, owner_key_id TEXT NOT NULL, status TEXT NOT NULL, media_type TEXT NOT NULL,
          container TEXT NOT NULL, codec TEXT NOT NULL, size_bytes INTEGER NOT NULL, duration REAL NOT NULL,
          width INTEGER NOT NULL, height INTEGER NOT NULL, fps REAL NOT NULL, total_frames INTEGER NOT NULL,
          staged_path TEXT, output_path TEXT, processed_frames INTEGER NOT NULL DEFAULT 0, error_code TEXT,
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL, expires_at TEXT NOT NULL)""")
        columns={row[1] for row in self._connection.execute("PRAGMA table_info(video_jobs)")}
        for name,kind in {"processing_phase":"TEXT","actual_frame_count":"INTEGER","frame_total_confirmed":"INTEGER NOT NULL DEFAULT 0","eligible_track_count":"INTEGER","classes_present":"TEXT","idempotency_key_hash":"TEXT","request_fingerprint":"TEXT"}.items():
            if name not in columns:self._connection.execute(f"ALTER TABLE video_jobs ADD COLUMN {name} {kind}")
        self._connection.executescript("""
          CREATE UNIQUE INDEX IF NOT EXISTS idx_video_intent ON video_jobs(owner_key_id,idempotency_key_hash) WHERE idempotency_key_hash IS NOT NULL;
          CREATE TABLE IF NOT EXISTS video_detections (
          job_id TEXT NOT NULL, frame_index INTEGER NOT NULL, track_id INTEGER NOT NULL,
          class_id INTEGER NOT NULL, class_name TEXT NOT NULL, confidence REAL NOT NULL,
          x_min INTEGER NOT NULL, y_min INTEGER NOT NULL, x_max INTEGER NOT NULL, y_max INTEGER NOT NULL,
          PRIMARY KEY(job_id, frame_index, track_id, class_id));
          CREATE INDEX IF NOT EXISTS idx_video_detections_page ON video_detections(job_id,frame_index,track_id);
          CREATE TABLE IF NOT EXISTS expired_video_jobs (
          job_id TEXT NOT NULL,owner_key_id TEXT NOT NULL,expired_at TEXT NOT NULL,PRIMARY KEY(job_id,owner_key_id));
        """);self._connection.commit();self.recover()
    def create(self,owner_key_id,metadata,staged_path,*,idempotency_key_hash=None,request_fingerprint=None):
        with self._lock,self._connection:
            self.cleanup()
            if idempotency_key_hash:
                row=self._connection.execute("SELECT * FROM video_jobs WHERE owner_key_id=? AND idempotency_key_hash=?",(owner_key_id,idempotency_key_hash)).fetchone()
                if row:
                    if row["request_fingerprint"]!=request_fingerprint:raise ApiError(409,"idempotency_conflict","The request conflicts with an existing intent.")
                    return self._row(row)
            if self._connection.execute("SELECT count(*) FROM video_jobs WHERE status='queued'").fetchone()[0]>=self.max_queued:raise ApiError(503,"queue_full","The video queue is currently full.")
            now=self.clock();job_id=str(uuid4())
            values={"job_id":job_id,"owner_key_id":owner_key_id,"status":"queued","media_type":metadata.media_type,"container":metadata.container,"codec":metadata.codec,"size_bytes":metadata.size_bytes,"duration":metadata.duration_seconds,"width":metadata.width,"height":metadata.height,"fps":metadata.fps,"total_frames":metadata.total_frames,"staged_path":str(staged_path),"created_at":now.isoformat(),"updated_at":now.isoformat(),"expires_at":(now+self.ttl).isoformat(),"processing_phase":"queued","idempotency_key_hash":idempotency_key_hash,"request_fingerprint":request_fingerprint}
            self._connection.execute("INSERT INTO video_jobs ("+",".join(values)+") VALUES ("+",".join("?" for _ in values)+")",tuple(values.values()))
            return self._row(self._connection.execute("SELECT * FROM video_jobs WHERE job_id=?",(job_id,)).fetchone())
    def get(self,job_id,owner_key_id):
        with self._lock:
            self.cleanup()
            row=self._connection.execute("SELECT * FROM video_jobs WHERE job_id=? AND owner_key_id=?",(job_id,owner_key_id)).fetchone()
            if row:return self._row(row)
            expired=self._connection.execute("SELECT 1 FROM expired_video_jobs WHERE job_id=? AND owner_key_id=?",(job_id,owner_key_id)).fetchone()
            raise ApiError(410 if expired else 404,"job_expired" if expired else "job_not_found","No accessible video job was found.")
    def cancel(self,job_id,owner_key_id):
        with self._lock,self._connection:
            job=self.get(job_id,owner_key_id)
            if not may_transition(job.status,VideoJobStatus.CANCELLED):raise ApiError(409,"job_terminal","The video job is already terminal.")
            self._connection.execute("UPDATE video_jobs SET status='cancelled',processing_phase='cancelled',updated_at=? WHERE job_id=?",(self.clock().isoformat(),job_id))
            return self.get(job_id,owner_key_id)
    def dequeue(self):
        with self._lock,self._connection:
            self.cleanup()
            row=self._connection.execute("SELECT * FROM video_jobs WHERE status='queued' ORDER BY created_at LIMIT 1").fetchone()
            if row is None:return None
            self._connection.execute("UPDATE video_jobs SET status='processing',processing_phase='frames',updated_at=? WHERE job_id=?",(self.clock().isoformat(),row["job_id"]))
            self._resources[row["job_id"]]={Path(row["staged_path"])} if row["staged_path"] else set()
            return self._row(self._connection.execute("SELECT * FROM video_jobs WHERE job_id=?",(row["job_id"],)).fetchone())
    def progress(self,job_id,processed_frames):
        with self._lock,self._connection:
            self._connection.execute("UPDATE video_jobs SET processed_frames=?,updated_at=? WHERE job_id=? AND status='processing' AND expires_at>?",(processed_frames,self.clock().isoformat(),job_id,self.clock().isoformat()))
    def phase(self,job_id,phase,actual_frame_count=None):
        if phase not in ("frames","encoding","publishing"):raise ValueError("invalid_phase")
        with self._lock,self._connection:
            if actual_frame_count is not None:
                self._connection.execute("UPDATE video_jobs SET actual_frame_count=?,total_frames=?,processed_frames=?,frame_total_confirmed=1 WHERE job_id=? AND status='processing'",(actual_frame_count,actual_frame_count,actual_frame_count,job_id))
            self._connection.execute("UPDATE video_jobs SET processing_phase=?,updated_at=? WHERE job_id=? AND status='processing' AND expires_at>?",(phase,self.clock().isoformat(),job_id,self.clock().isoformat()))
    def confirm_frames(self,job_id,count):self.phase(job_id,"encoding",count)
    def is_cancelled(self,job_id):
        with self._lock:
            row=self._connection.execute("SELECT status,expires_at FROM video_jobs WHERE job_id=?",(job_id,)).fetchone()
            return row is None or row["status"] in ("cancelled","failed") or datetime.fromisoformat(row["expires_at"])<=self.clock()
    def register_path(self,job_id,path):
        with self._lock:self._resources.setdefault(job_id,set()).add(path)
    def in_use(self,path):
        with self._lock:return any(path in paths for paths in self._resources.values())
    def release(self,job_id):
        with self._lock:
            paths=self._resources.pop(job_id,set())
            row=self._connection.execute("SELECT status,expires_at FROM video_jobs WHERE job_id=?",(job_id,)).fetchone()
            if row is None or row["status"] in ("cancelled","failed") or datetime.fromisoformat(row["expires_at"])<=self.clock():self._purged.update(paths)
    def finish(self,job_id,output_path,detections,actual_frame_count=None,eligible_classes=(),owner_key_id=None):
        with self._lock,self._connection:
            row=self._connection.execute("SELECT * FROM video_jobs WHERE job_id=?",(job_id,)).fetchone()
            if row is None:return "expired"
            if owner_key_id is not None and row["owner_key_id"]!=owner_key_id:return "failed"
            if datetime.fromisoformat(row["expires_at"])<=self.clock():self.cleanup();return "expired"
            if row["status"]!="processing":return row["status"]
            if actual_frame_count is not None and actual_frame_count<=0:return "failed"
            self._connection.executemany("INSERT OR REPLACE INTO video_detections VALUES (?,?,?,?,?,?,?,?,?,?)",[(job_id,d.frame_index,d.track_id,d.class_id,d.class_name,d.confidence,d.x_min,d.y_min,d.x_max,d.y_max) for d in detections])
            if datetime.fromisoformat(row["expires_at"])<=self.clock():self.cleanup();return "expired"
            confirmed=actual_frame_count is not None
            eligible=len({d.track_id for d in detections if d.class_name.strip().lower() in eligible_classes}) if confirmed else None
            classes=json.dumps(sorted({d.class_name for d in detections})) if confirmed else None
            self._connection.execute("UPDATE video_jobs SET status='completed',output_path=?,processing_phase=?,actual_frame_count=?,frame_total_confirmed=?,eligible_track_count=?,classes_present=?,updated_at=? WHERE job_id=?",(str(output_path),"ready" if confirmed else None,actual_frame_count,int(confirmed),eligible,classes,self.clock().isoformat(),job_id))
            if confirmed:self._connection.execute("UPDATE video_jobs SET total_frames=?,processed_frames=? WHERE job_id=?",(actual_frame_count,actual_frame_count,job_id))
            return "completed"
    def fail(self,job_id,error_code):
        with self._lock,self._connection:
            self._connection.execute("UPDATE video_jobs SET status='failed',processing_phase='failed',error_code=?,updated_at=? WHERE job_id=? AND status='processing'",(error_code,self.clock().isoformat(),job_id))
    def all_detections(self,job_id,owner_key_id):
        with self._lock:
            job=self.get(job_id,owner_key_id)
            if job.status is not VideoJobStatus.COMPLETED:raise ApiError(409,"source_not_ready","The source is not ready.")
            return [FrameDetection(*tuple(row)[1:]) for row in self._connection.execute("SELECT * FROM video_detections WHERE job_id=? ORDER BY frame_index,track_id",(job_id,))]
    def detections(self,job_id,owner_key_id,page,page_size):
        with self._lock:
            job=self.get(job_id,owner_key_id)
            if job.status is not VideoJobStatus.COMPLETED:raise ApiError(409,"result_not_ready","The video result is not available.")
            total=self._connection.execute("SELECT count(*) FROM video_detections WHERE job_id=?",(job_id,)).fetchone()[0]
            rows=self._connection.execute("SELECT * FROM video_detections WHERE job_id=? ORDER BY frame_index,track_id LIMIT ? OFFSET ?",(job_id,page_size,(page-1)*page_size)).fetchall()
            return [FrameDetection(*tuple(row)[1:]) for row in rows],total
    def summary(self,job_id,owner_key_id):
        with self._lock:
            job=self.get(job_id,owner_key_id)
            if job.status is not VideoJobStatus.COMPLETED:raise ApiError(409,"result_not_ready","The video result is not available.")
            return {row["class_name"]:row["total"] for row in self._connection.execute("SELECT class_name,count(*) AS total FROM video_detections WHERE job_id=? GROUP BY class_name ORDER BY class_name",(job_id,))}
    def recover(self):
        with self._lock,self._connection:
            rows=self._connection.execute("SELECT job_id,output_path FROM video_jobs WHERE status='processing'").fetchall()
            for row in rows:
                self._connection.execute("DELETE FROM video_detections WHERE job_id=?",(row["job_id"],))
                if row["output_path"]:self._purged.add(Path(row["output_path"]))
            self._connection.execute("UPDATE video_jobs SET status='queued',processing_phase='queued',processed_frames=0,actual_frame_count=NULL,frame_total_confirmed=0,output_path=NULL,eligible_track_count=NULL,classes_present=NULL,updated_at=? WHERE status='processing' AND expires_at>?",(self.clock().isoformat(),self.clock().isoformat()))
            self.cleanup()
    def cleanup(self):
        with self._lock,self._connection:
            rows=self._connection.execute("SELECT job_id,owner_key_id,staged_path,output_path FROM video_jobs WHERE expires_at<=?",(self.clock().isoformat(),)).fetchall()
            for row in rows:
                self._connection.execute("DELETE FROM video_detections WHERE job_id=?",(row["job_id"],))
                self._connection.execute("INSERT OR REPLACE INTO expired_video_jobs VALUES (?,?,?)",(row["job_id"],row["owner_key_id"],self.clock().isoformat()))
                self._purged.update(Path(p) for p in (row["staged_path"],row["output_path"]) if p)
            self._connection.execute("DELETE FROM video_jobs WHERE expires_at<=?",(self.clock().isoformat(),))
            return list(self._purged)
    def acknowledge_cleanup(self,path):
        with self._lock:self._purged.discard(path)
    def close(self):
        with self._lock:self._connection.close()
    @staticmethod
    def _row(row):
        m=VideoMetadata(row["media_type"],row["container"],row["codec"],row["size_bytes"],row["duration"],row["width"],row["height"],row["fps"],row["total_frames"])
        metadata={"width":m.width,"height":m.height,"fps":m.fps,"frame_count":row["actual_frame_count"],"duration_seconds":row["actual_frame_count"]/m.fps,"timebase":"processed-cfr"} if row["status"]=="completed" and row["actual_frame_count"] else None
        return VideoJob(row["job_id"],row["owner_key_id"],VideoJobStatus(row["status"]),m,datetime.fromisoformat(row["created_at"]),datetime.fromisoformat(row["updated_at"]),datetime.fromisoformat(row["expires_at"]),Path(row["staged_path"]) if row["staged_path"] else None,Path(row["output_path"]) if row["output_path"] else None,row["processed_frames"],row["error_code"],processing_phase=row["processing_phase"],frame_total_confirmed=bool(row["frame_total_confirmed"]),video_metadata=metadata,eligible_track_count=row["eligible_track_count"],classes_present=json.loads(row["classes_present"]) if row["classes_present"] else None)
