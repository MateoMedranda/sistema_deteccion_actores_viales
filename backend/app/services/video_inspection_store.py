"""Transactional admission, fixed expiry and bounded immutable inspection assets."""
from datetime import datetime,timedelta,UTC
from pathlib import Path
from uuid import uuid4
import json
from app.api.error_handlers import ApiError
from app.services.video_detail_access import parent
from app.services.video_progressive_store import dump,now

class InspectionStore:
 def __init__(self,store,settings):
  self.store,self.settings=store,settings
  self.directory=settings.video_temp_dir/'inspections';self.directory.mkdir(parents=True,exist_ok=True)
  with store.lock,store.db:
   store.db.execute('CREATE TABLE IF NOT EXISTS p_video_inspections(id TEXT PRIMARY KEY,job TEXT,generation TEXT,track INTEGER,idx INTEGER,policy TEXT,expires TEXT,state TEXT,payload TEXT,paths TEXT DEFAULT \'{}\',bytes INTEGER DEFAULT 0,UNIQUE(job,generation,track,idx,policy))')
   store.db.execute("UPDATE p_video_inspections SET state='failed',payload=json_set(payload,'$.state','failed','$.error_code','inspection_interrupted') WHERE state='processing'")
   store.db.execute("UPDATE p_video_inspections SET state='queued' WHERE state='preparing'")
  if not hasattr(store,'detail_resources'):store.detail_resources=[]
  store.detail_resources.append(self)

 def get_record(self,job,owner,iid):
  parent(self.store,job,owner)
  record=self.store.db.execute('SELECT * FROM p_video_inspections WHERE id=? AND job=?',(iid,job)).fetchone()
  if record is None:raise ApiError(404,'inspection_not_found','The inspection is unavailable.')
  if datetime.fromisoformat(record['expires'])<=now():raise ApiError(410,'inspection_expired','The inspection expired.')
  return record

 def get(self,job,owner,iid):
  with self.store.lock:return json.loads(self.get_record(job,owner,iid)['payload'])

 def admit(self,job,owner,body):
  s=self.store;cfg=self.settings
  with s.lock,s.db:
   row=parent(s,job,owner,body['generation']);generation=row['generation']
   old=s.db.execute('SELECT id FROM p_video_inspections WHERE job=? AND generation=? AND track=? AND idx=? AND policy=?',(job,generation,body['track_id'],body['frame_index'],'selected-frame-v1')).fetchone()
   if old:return self.get(job,owner,old['id'])
   if s.db.execute("SELECT count(*) FROM p_video_inspections WHERE state IN ('queued','preparing')").fetchone()[0]>=cfg.video_inspection_max_queued:raise ApiError(429,'inspection_queue_full','The inspection queue is full.')
   total,used=s.db.execute('SELECT count(*),coalesce(sum(bytes),0) FROM p_video_inspections WHERE job=?',(job,)).fetchone()
   reserve=cfg.video_inspection_max_resource_bytes*2+2*1024**2
   if total>=cfg.video_inspection_max_contexts_per_job or used+reserve>cfg.video_inspection_max_bytes_per_job:raise ApiError(429,'inspection_quota','Inspection capacity reached.')
   rec=s.db.execute('SELECT payload FROM p_frames WHERE job=? AND idx=?',(job,body['frame_index'])).fetchone()
   if rec is None:raise ApiError(409,'interval_not_ready','The frame is not confirmed.')
   frame=json.loads(rec[0]);ob=next((o for o in frame['observations'] if o['track_id']==body['track_id']),None)
   if ob is None:raise ApiError(404,'inspection_not_found','The vehicle is not present in this frame.')
   iid=str(uuid4());expires=min(datetime.fromisoformat(row['expires']),now()+timedelta(seconds=cfg.enrichment_result_ttl_seconds)).isoformat()
   measured=frame.get('detection_performed') is True
   value=dict(job_id=job,generation=generation,inspection_id=iid,policy_version='selected-frame-v1',track_id=body['track_id'],frame_index=body['frame_index'],time_us=frame['start_us'],end_us=frame['end_us'],class_name=ob['class_name'][:256],bbox=ob['raw_bbox'],observation_kind='measured' if measured else 'predicted',confidence=ob['confidence'],confidence_kind='measured' if measured else 'last_measured',state='queued',result_revision=0,vehicle=None,plate_asset=None,attributes=dict(status='pending',items=[],error_code=None),plate=dict(status='pending',text=None,ocr_confidence=None,inspection_id=iid,policy_id='baseline-v1',used_enhancement=False,error_code=None),plate_preview_url=None,plate_preview_profiles=[],error_code=None,expires_at=expires)
   s.db.execute('INSERT INTO p_video_inspections(id,job,generation,track,idx,policy,expires,state,payload,bytes) VALUES(?,?,?,?,?,?,?,?,?,?)',(iid,job,generation,body['track_id'],body['frame_index'],'selected-frame-v1',expires,'queued',dump(value),reserve))
   return value

 def paths(self,job):
  result=[]
  for rec in self.store.db.execute('SELECT paths FROM p_video_inspections WHERE job=?',(job,)):
   result.extend(Path(p) for p in json.loads(rec[0]).values())
  return result

 def purge(self,job):self.store.db.execute('DELETE FROM p_video_inspections WHERE job=?',(job,))

 def cleanup(self):
  s=self.store
  with s.lock,s.db:
   for rec in s.db.execute('SELECT * FROM p_video_inspections WHERE expires<=?',(now().isoformat(),)).fetchall():
    paths=[Path(p) for p in json.loads(rec['paths']).values()]
    if any(s.readers.get(str(p)) for p in paths):continue
    for p in paths:p.unlink(missing_ok=True)
    # Canonical columns and expiry remain as admission-counting tombstone until parent expiry.
    s.db.execute("UPDATE p_video_inspections SET paths='{}',payload='{}',bytes=0,state='expired' WHERE id=?",(rec['id'],))
