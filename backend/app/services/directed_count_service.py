import json
from app.api.error_handlers import ApiError
from app.services.video_detail_access import parent
from app.services.video_progressive_store import dump
from app.services.directed_count_store import initialize
from app.services.directed_counting import advance
from app.services.video_observation_provenance import measured
from app.domain.vehicle_taxonomy import normalize_class

class DirectedCountService:
 def __init__(self,store):
  self.store=store;initialize(store)
  if not hasattr(store,'detail_resources'):store.detail_resources=[]
  store.detail_resources.append(self)
 def paths(self,job):return []
 def purge(self,job):
  for table in ['p_directed_count_state','p_directed_count_tracks','p_directed_count_events']:self.store.db.execute('DELETE FROM '+table+' WHERE job=?',(job,))
 def configure(self,job,owner,body):
  s=self.store
  with s.lock,s.db:
   source=parent(s,job,owner,body['generation']);old=s.db.execute('SELECT * FROM p_directed_count_state WHERE job=?',(job,)).fetchone()
   revision=old['revision'] if old else 0
   if body['expected_revision']!=revision:raise ApiError(409,'count_revision_changed','Reload the current configuration.')
   line=dump(body['line']);direction=body['direction']
   if old is None or line!=old['line'] or direction!=old['direction']:
    s.db.execute('INSERT OR REPLACE INTO p_directed_count_state(job,generation,revision,line,direction) VALUES(?,?,?,?,?)',(job,source['generation'],revision+1,line,direction))
    for table in ['p_directed_count_tracks','p_directed_count_events']:s.db.execute('DELETE FROM '+table+' WHERE job=?',(job,))
   return self.snapshot(job,owner,source['generation'],0)
 def disable(self,job,owner,generation,expected):
  s=self.store
  with s.lock,s.db:
   parent(s,job,owner,generation);old=s.db.execute('SELECT * FROM p_directed_count_state WHERE job=?',(job,)).fetchone()
   if expected!=(old['revision'] if old else 0):raise ApiError(409,'count_revision_changed','Reload the current configuration.')
   if old and old['line'] is not None:
    s.db.execute('UPDATE p_directed_count_state SET line=NULL,direction=NULL,revision=revision+1,cursor=0,covered=0,error=NULL WHERE job=?',(job,))
    for table in ['p_directed_count_tracks','p_directed_count_events']:s.db.execute('DELETE FROM '+table+' WHERE job=?',(job,))
 def snapshot(self,job,owner,generation,at_us=0,revision=None):
  s=self.store
  with s.lock:
   source=parent(s,job,owner,generation);state=s.db.execute('SELECT * FROM p_directed_count_state WHERE job=?',(job,)).fetchone();rev=state['revision'] if state else 0
   if revision is not None and revision!=rev:raise ApiError(409,'count_revision_changed','Reload the current configuration.')
   if at_us and at_us>=source['until_us']:raise ApiError(409,'interval_not_ready','The interval is unavailable.')
   enabled=bool(state and state['line']);covered=state['covered'] if state else 0
   ready=enabled and not state['error'] and at_us<covered and at_us<source['until_us']
   total=s.db.execute('SELECT count(*) FROM p_directed_count_events WHERE job=? AND revision=? AND time_us<=?',(job,rev,at_us)).fetchone()[0] if ready else 0 if not enabled else None
   return dict(job_id=job,generation=source['generation'],policy_version='finite-center-v1',revision=rev,enabled=enabled,line=json.loads(state['line']) if enabled else None,direction=state['direction'] if enabled else None,status='disabled' if not enabled else 'unavailable' if state['error'] else 'ready' if ready else 'pending',at_us=at_us,available_until_us=source['until_us'],covered_until_us=covered,total=total,error_code=state['error'] if state else None,expires_at=source['expires'])
 def reduce(self,job,limit=200):
  s=self.store
  with s.lock,s.db:
   source=s.row(job);state=s.db.execute('SELECT * FROM p_directed_count_state WHERE job=?',(job,)).fetchone()
   if not state or not state['line'] or state['error']:return
   line=json.loads(state['line']);size=json.loads(source['timeline']);points=[(line[k]['x']*size['width'],line[k]['y']*size['height']) for k in ['point_a','point_b']]
   records=s.db.execute('SELECT payload FROM p_frames WHERE job=? AND idx>=? ORDER BY idx LIMIT ?',(job,state['cursor'],min(200,limit))).fetchall()
   changed={};cursor=state['cursor'];covered=state['covered']
   for record in records:
    f=json.loads(record[0]);obs=measured(s,job,f)
    if obs is None:
     s.db.execute("UPDATE p_directed_count_state SET error='reanalysis_required' WHERE job=?",(job,));return
    for ob in obs:
     tid=ob['track_id']
     if tid not in changed:
      old=s.db.execute('SELECT payload FROM p_directed_count_tracks WHERE job=? AND revision=? AND track=?',(job,state['revision'],tid)).fetchone();changed[tid]=json.loads(old[0]) if old else {}
     b=ob['raw_bbox'];point=((b['x_min']+b['x_max'])/2,(b['y_min']+b['y_max'])/2)
     changed[tid],event=advance(changed[tid],point,points,state['direction'],ob['class_name'])
     if event:s.db.execute('INSERT OR IGNORE INTO p_directed_count_events VALUES(?,?,?,?,?,?)',(job,state['revision'],tid,f['start_us'],f['frame_index'],normalize_class(ob['class_name'])))
    cursor=f['frame_index']+1;covered=f['end_us']
   s.db.executemany('INSERT OR REPLACE INTO p_directed_count_tracks VALUES(?,?,?,?)',[(job,state['revision'],tid,dump(value)) for tid,value in changed.items()])
   s.db.execute('UPDATE p_directed_count_state SET cursor=?,covered=? WHERE job=?',(cursor,covered,job))
