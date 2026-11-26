"""Cooperative fair reduction: capture under lock, geometry outside, CAS commit."""
import json,time
from app.services.video_observation_provenance import measured
from app.services.directed_counting import advance
from app.domain.vehicle_taxonomy import normalize_class
from app.services.video_progressive_store import dump
class CountLinesReducer:
 def __init__(self,service):
  self.service=service;self.turn={};self.last_metrics={};service.store.detail_resources.append(self)
 def paths(self,job):return []
 def purge(self,job):self.turn.pop(job,None)
 def reduce(self,job):
  service=self.service;s=service.store;cfg=service.settings;start=time.perf_counter()
  with s.lock:
   lock_start=time.perf_counter();source=s.row(job);g=source['generation'];all_lines=[l for l in service._lines(job,g) if not l['error'] and l['cursor']<source['frames']]
   if not all_lines:return
   offset=self.turn.get(job,0)%len(all_lines);base=all_lines[offset];self.turn[job]=offset+1
   lines=[l for l in all_lines[offset:]+all_lines[:offset] if l['cursor']==base['cursor']][:cfg.video_count_reducer_max_pairs]
   count=min(cfg.video_count_reducer_batch_frames,max(1,cfg.video_count_reducer_max_pairs//len(lines)))
   lengths=s.db.execute('SELECT idx,length(CAST(payload AS BLOB)) AS size FROM p_frames WHERE job=? AND idx>=? ORDER BY idx LIMIT ?',(job,base['cursor'],count)).fetchall();size=0;accepted=[]
   for row in lengths:
    if size+row['size']>2*1024*1024:break
    size+=row['size'];accepted.append(row['idx'])
   if not accepted:
    with s.db:
     for l in lines:s.db.execute("UPDATE p_count_lines SET error='count_work_limit' WHERE job=? AND generation=? AND line_id=? AND geometry_revision=?",(job,g,l['line_id'],l['geometry_revision']))
    return
   frames=[json.loads(r[0]) for r in s.db.execute('SELECT payload FROM p_frames WHERE job=? AND idx>=? AND idx<=? ORDER BY idx',(job,accepted[0],accepted[-1]))]
   observations=[measured(s,job,f) for f in frames]
   if any(o is None for o in observations):
    with s.db:
     for l in lines:s.db.execute("UPDATE p_count_lines SET error='reanalysis_required' WHERE job=? AND generation=? AND line_id=?",(job,g,l['line_id']))
    return
   tids={ob['track_id'] for obs in observations for ob in obs};states={};geometry={};dimensions=json.loads(source['timeline'])
   for l in lines:
    lid=l['line_id'];states[lid]={}
    ids=list(tids)
    for begin in range(0,len(ids),500):
     group=ids[begin:begin+500]
     query='SELECT track,payload FROM p_count_lines_tracks WHERE job=? AND generation=? AND line_id=? AND geometry_revision=? AND track IN ('+','.join('?'*len(group))+')'
     for row in s.db.execute(query,(job,g,lid,l['geometry_revision'],*group)):states[lid][row[0]]=json.loads(row[1])
    segment=json.loads(l['segment']);geometry[lid]=[(segment[k]['x']*dimensions['width'],segment[k]['y']*dimensions['height']) for k in ['point_a','point_b']]
   capture_ms=(time.perf_counter()-lock_start)*1000
  events={l['line_id']:[] for l in lines};tick=time.perf_counter();completed=[]
  for f,obs in zip(frames,observations):
   for l in lines:
    lid=l['line_id']
    for ob in obs:
     tid=ob['track_id'];box=ob['raw_bbox'];point=((box['x_min']+box['x_max'])/2,(box['y_min']+box['y_max'])/2)
     states[lid][tid],event=advance(states[lid].get(tid,{}),point,geometry[lid],'both',ob['class_name'])
     if event:events[lid].append((job,g,lid,l['geometry_revision'],tid,f['start_us'],f['frame_index'],normalize_class(ob['class_name'])))
   completed.append(f)
   if (time.perf_counter()-tick)*1000>=cfg.video_count_reducer_budget_ms:break
  compute_ms=(time.perf_counter()-tick)*1000
  with s.lock:
   commit_start=time.perf_counter()
   with s.db:
    current=s.row(job)
    if current['generation']!=g:return
    for l in lines:
     lid=l['line_id'];actual=s.db.execute('SELECT * FROM p_count_lines WHERE job=? AND generation=? AND line_id=?',(job,g,lid)).fetchone()
     if not actual or actual['deleted'] or actual['geometry_revision']!=l['geometry_revision'] or actual['cursor']!=l['cursor']:continue
     s.db.executemany('INSERT OR REPLACE INTO p_count_lines_tracks VALUES(?,?,?,?,?,?)',[(job,g,lid,l['geometry_revision'],tid,dump(value)) for tid,value in states[lid].items()])
     s.db.executemany('INSERT OR IGNORE INTO p_count_lines_events VALUES(?,?,?,?,?,?,?,?)',events[lid])
     last=completed[-1];s.db.execute('UPDATE p_count_lines SET cursor=?,covered=? WHERE job=? AND generation=? AND line_id=?',(last['frame_index']+1,last['end_us'],job,g,lid))
   commit_ms=(time.perf_counter()-commit_start)*1000
  self.last_metrics=dict(compute_ms=compute_ms,capture_lock_ms=capture_ms,commit_lock_ms=commit_ms,total_ms=(time.perf_counter()-start)*1000,frame_line_pairs=len(completed)*len(lines))
