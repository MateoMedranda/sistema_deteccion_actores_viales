"""Incremental per-identity class votes, independent of OCR, line and playhead."""
import json
from app.services.detection_inventory_store import initialize
from app.services.video_progressive_store import dump
from app.services.video_detail_access import parent
from app.services.video_observation_provenance import measured
from app.domain.vehicle_taxonomy import VEHICLE_CLASSES,normalize_class
from app.services.class_presentation import class_presentation

class DetectionInventory:
 def __init__(self,store):
  self.store=store;initialize(store)
  if not hasattr(store,'detail_resources'):store.detail_resources=[]
  store.detail_resources.append(self)
 def paths(self,job):return []
 def purge(self,job):
  for table in ['p_detection_inventory','p_detection_tracks','p_detection_votes']:self.store.db.execute('DELETE FROM '+table+' WHERE job=?',(job,))
 def publish(self,row,frames):
  """Caller owns the publication transaction. Process newly inserted frames only."""
  s=self.store;job=row['job'];generation=row['generation']
  s.db.execute('INSERT OR IGNORE INTO p_detection_inventory(job,generation) VALUES(?,?)',(job,generation))
  state=s.db.execute('SELECT * FROM p_detection_inventory WHERE job=?',(job,)).fetchone()
  if state['error']:return
  # Older prefix is backfilled by the worker before new publication can catch up.
  frames=[f for f in frames if f['frame_index']>=state['cursor']]
  if not frames or frames[0]['frame_index']!=state['cursor']:return
  votes={};tracks={};cursor=state['cursor'];covered=state['covered']
  for f in frames:
   if f['frame_index']!=cursor:break
   observations=measured(s,job,f)
   if observations is None:
    s.db.execute("UPDATE p_detection_inventory SET error='reanalysis_required' WHERE job=?",(job,));return
   for ob in observations:
    tid=ob['track_id'];key=normalize_class(ob['class_name']);pair=(tid,key);old=votes.get(pair,(0,0));votes[pair]=(old[0]+1,max(old[1],ob['confidence']))
    old=tracks.get(tid,(f['start_us'],f['start_us'],0));tracks[tid]=(min(old[0],f['start_us']),max(old[1],f['start_us']),old[2]+1)
   cursor=f['frame_index']+1;covered=f['end_us']
  s.db.executemany('INSERT INTO p_detection_votes VALUES(?,?,?,?,?,?) ON CONFLICT(job,generation,track,class_key) DO UPDATE SET count=count+excluded.count,max_confidence=max(max_confidence,excluded.max_confidence)',[(job,generation,tid,key,n,confidence) for (tid,key),(n,confidence) in votes.items()])
  for tid,(first,last,n) in tracks.items():
   winner=s.db.execute('SELECT class_key FROM p_detection_votes WHERE job=? AND generation=? AND track=? ORDER BY count DESC,max_confidence DESC,class_key ASC LIMIT 1',(job,generation,tid)).fetchone()[0]
   s.db.execute('INSERT INTO p_detection_tracks VALUES(?,?,?,?,?,?,?) ON CONFLICT(job,generation,track) DO UPDATE SET canonical_class=excluded.canonical_class,first_seen=min(first_seen,excluded.first_seen),last_seen=max(last_seen,excluded.last_seen),measured_observations=measured_observations+excluded.measured_observations',(job,generation,tid,winner,first,last,n))
  s.db.execute('UPDATE p_detection_inventory SET cursor=?,covered=?,revision=revision+1 WHERE job=?',(cursor,covered,job))
 def backfill(self,job):
  s=self.store
  with s.lock,s.db:
   row=s.row(job);state=s.db.execute('SELECT * FROM p_detection_inventory WHERE job=?',(job,)).fetchone();cursor=state['cursor'] if state else 0
   if state and state['error']:return
   frames=[json.loads(r[0]) for r in s.db.execute('SELECT payload FROM p_frames WHERE job=? AND idx>=? ORDER BY idx LIMIT 200',(job,cursor))]
   if frames or state is None:self.publish(row,frames)
 def snapshot(self,job,owner,generation):
  s=self.store
  with s.lock:
   row=parent(s,job,owner,generation);state=s.db.execute('SELECT * FROM p_detection_inventory WHERE job=?',(job,)).fetchone()
   covered=state['covered'] if state else 0;cursor=state['cursor'] if state else 0;error=state['error'] if state else None
   classes=[];excluded=0
   for key,count in s.db.execute('SELECT canonical_class,count(*) FROM p_detection_tracks WHERE job=? GROUP BY canonical_class ORDER BY canonical_class',(job,)):
    if key=='person':excluded+=count;continue
    presentation=class_presentation(key);review=key not in VEHICLE_CLASSES
    classes.append(dict(class_key=key,label=presentation['label'] if not review else ('Sin clasificar' if key=='unknown' else key),color=presentation['color'],track_count=count,requires_review=review))
   status='unavailable' if error else 'building' if cursor<row['frames'] or state is None else 'final' if row['analysis']=='complete' else 'partial'
   return dict(job_id=job,generation=row['generation'],policy_version='vehicle-inventory-v1',status=status,revision=state['revision'] if state else 0,covered_frames=cursor,covered_until_us=covered,available_until_us=row['until_us'],analysis_complete=row['analysis']=='complete',total_tracks=None if error else sum(c['track_count'] for c in classes),classes=classes,excluded_nonvehicle_tracks=excluded,requires_review=any(c['requires_review'] for c in classes),error_code=error,expires_at=row['expires'])
