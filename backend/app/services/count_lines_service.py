"""Bidirectional collections. Reads never create, reduce or import."""
import hashlib,json
from types import SimpleNamespace
from uuid import uuid5,NAMESPACE_URL
from app.api.error_handlers import ApiError
from app.domain.count_lines import CollectionWrite
from app.services.video_detail_access import parent
from app.services.video_progressive_store import dump
from app.services.count_lines_store import CountLinesStore
PALETTE=['#F59E0B', '#06B6D4', '#EF4444', '#8B5CF6', '#10B981', '#EC4899', '#F97316', '#3B82F6', '#84CC16', '#14B8A6', '#A855F7', '#EAB308', '#0EA5E9', '#F43F5E', '#22C55E', '#D946EF', '#FB923C', '#6366F1', '#A3E635', '#2DD4BF', '#C084FC', '#FACC15', '#38BDF8', '#FB7185', '#4ADE80', '#E879F9', '#EA580C', '#4F46E5', '#65A30D', '#0D9488', '#7C3AED', '#CA8A04']
PROTOCOL=dict(protocol='video-count-lines-v1',policy_version='finite-center-both-v1')
def reject(code):raise ApiError(409,code,'Reload or correct the count line configuration.')
class CountLinesService:
 def __init__(self,store,settings=None):
  self.store=store;self.settings=settings or SimpleNamespace(video_count_max_lines=10,video_count_max_admitted_lines=128,video_count_reducer_batch_frames=20,video_count_reducer_max_pairs=200,video_count_reducer_budget_ms=5)
  self.storage=CountLinesStore(store)
  from app.services.count_lines_reducer import CountLinesReducer
  self.reducer=CountLinesReducer(self)
 def _collection(self,job):return self.store.db.execute('SELECT * FROM p_count_lines_collection WHERE job=?',(job,)).fetchone()
 def _lines(self,job,generation):return self.store.db.execute('SELECT * FROM p_count_lines WHERE job=? AND generation=? AND deleted=0 ORDER BY ordinal',(job,generation)).fetchall()
 def _legacy(self,job):
  s=self.store
  if not s.db.execute("SELECT 1 FROM sqlite_master WHERE name='p_directed_count_state'").fetchone():return None
  return s.db.execute('SELECT * FROM p_directed_count_state WHERE job=? AND line IS NOT NULL',(job,)).fetchone()
 def descriptor(self,job,owner,generation):
  s=self.store
  with s.lock:
   source=parent(s,job,owner,generation);c=self._collection(job);lines=self._lines(job,generation)
   return dict(job_id=job,generation=generation,**PROTOCOL,mode='both',revision=c['revision'] if c else 0,admitted_count=c['admitted'] if c else 0,limits=dict(max_active_lines=self.settings.video_count_max_lines,max_admitted_lines=self.settings.video_count_max_admitted_lines,max_name_graphemes=60,max_name_utf8_bytes=2048,max_name_codepoints=1024),default_colors=PALETTE,lines=[dict(line_id=l['line_id'],name=l['name'],color=l['color'],segment=json.loads(l['segment']),geometry_revision=l['geometry_revision'],origin=l['origin']) for l in lines],legacy_import=dict(status='imported' if c and c['imported'] else 'offered' if self._legacy(job) else 'none',line_id=c['import_id'] if c and c['imported'] else None),expires_at=source['expires'])
 def configure(self,job,owner,body):
  with self.store.lock,self.store.db:return self._apply(job,owner,body)
 def _apply(self,job,owner,body):
  body=CollectionWrite.model_validate(body).model_dump(mode='json');g=body['generation'];s=self.store;parent(s,job,owner,g)
  c=self._collection(job);revision=c['revision'] if c else 0;expected=body['expected_revision']
  canonical={**body,'lines':sorted(body['lines'],key=lambda l:l['line_id'])};digest=hashlib.sha256(json.dumps(canonical,sort_keys=True,separators=(',',':')).encode()).hexdigest()
  if expected!=revision:
   if c and revision==expected+1 and c['last_expected']==expected and c['last_hash']==digest:return self.descriptor(job,owner,g)
   reject('count_revision_changed')
  incoming={l['line_id']:l for l in body['lines']};old={l['line_id']:l for l in self._lines(job,g)}
  for key in ['name','color']:
   values=[l[key].casefold() if key=='name' else l[key] for l in incoming.values()]
   if len(values)!=len(set(values)):reject('count_'+key+'_conflict')
  new=set(incoming)-set(old);admitted=c['admitted'] if c else 0
  if new and len(incoming)>self.settings.video_count_max_lines:reject('count_line_limit')
  if admitted+len(new)>self.settings.video_count_max_admitted_lines and new:reject('count_line_admission_limit')
  for lid in new:
   if s.db.execute('SELECT 1 FROM p_count_lines WHERE job=? AND generation=? AND line_id=?',(job,g,lid)).fetchone():reject('count_line_deleted')
  if set(old)==set(incoming) and all(old[lid]['name']==l['name'] and old[lid]['color']==l['color'] and json.loads(old[lid]['segment'])==l['segment'] for lid,l in incoming.items()):return self.descriptor(job,owner,g)
  if revision>=2**53-1:reject('count_revision_changed')
  ordinal=c['ordinal'] if c else 0
  # Release unique reservations INSIDE the transaction, allowing atomic swaps.
  for lid in old:s.db.execute('UPDATE p_count_lines SET name_key=?,color=? WHERE job=? AND generation=? AND line_id=?',('\0'+lid,'!'+lid,job,g,lid))
  for lid in set(old)-set(incoming):
   s.db.execute("UPDATE p_count_lines SET deleted=1,name=NULL,name_key=NULL,color=NULL,segment=NULL,error=NULL WHERE job=? AND generation=? AND line_id=?",(job,g,lid))
   for table in ['p_count_lines_tracks','p_count_lines_events']:s.db.execute('DELETE FROM '+table+' WHERE job=? AND generation=? AND line_id=?',(job,g,lid))
  for lid,l in incoming.items():
   if lid not in old:
    ordinal+=1
    s.db.execute('INSERT INTO p_count_lines(job,generation,line_id,name,name_key,color,segment,ordinal,geometry_revision) VALUES(?,?,?,?,?,?,?,?,1)',(job,g,lid,l['name'],l['name'].casefold(),l['color'],dump(l['segment']),ordinal))
   else:
    changed=json.loads(old[lid]['segment'])!=l['segment']
    if changed:
     for table in ['p_count_lines_tracks','p_count_lines_events']:s.db.execute('DELETE FROM '+table+' WHERE job=? AND generation=? AND line_id=?',(job,g,lid))
    s.db.execute('UPDATE p_count_lines SET name=?,name_key=?,color=?,segment=?,geometry_revision=geometry_revision+?,cursor=?,covered=?,error=? WHERE job=? AND generation=? AND line_id=?',(l['name'],l['name'].casefold(),l['color'],dump(l['segment']),int(changed),0 if changed else old[lid]['cursor'],0 if changed else old[lid]['covered'],None if changed else old[lid]['error'],job,g,lid))
  if c:s.db.execute('UPDATE p_count_lines_collection SET revision=?,admitted=?,ordinal=?,last_expected=?,last_hash=? WHERE job=?',(revision+1,admitted+len(new),ordinal,expected,digest,job))
  else:s.db.execute('INSERT INTO p_count_lines_collection(job,generation,revision,admitted,ordinal,last_expected,last_hash) VALUES(?,?,?,?,?,?,?)',(job,g,1,len(new),ordinal,expected,digest))
  return self.descriptor(job,owner,g)
 def import_legacy(self,job,owner,body):
  s=self.store;g=str(body['generation'])
  with s.lock,s.db:
   parent(s,job,owner,g);c=self._collection(job)
   if c and c['imported']:return self.descriptor(job,owner,g)
   if self._lines(job,g):reject('legacy_import_conflict')
   legacy=self._legacy(job)
   if legacy is None:reject('legacy_line_unavailable')
   fingerprint=hashlib.sha256(legacy['line'].encode()).hexdigest();lid=str(uuid5(NAMESPACE_URL,job+g+fingerprint))
   self._apply(job,owner,dict(generation=g,expected_revision=body['expected_revision'],lines=[dict(line_id=lid,name='Línea 1',color=PALETTE[0],segment=json.loads(legacy['line']))]))
   s.db.execute('UPDATE p_count_lines_collection SET imported=1,import_id=?,import_fingerprint=? WHERE job=?',(lid,fingerprint,job));s.db.execute("UPDATE p_count_lines SET origin='legacy_import' WHERE job=? AND generation=? AND line_id=?",(job,g,lid))
   return self.descriptor(job,owner,g)
 def snapshot(self,job,owner,generation,revision,at_us):
  s=self.store
  with s.lock:
   source=parent(s,job,owner,generation);c=self._collection(job)
   if revision!=(c['revision'] if c else 0):reject('count_revision_changed')
   if at_us and at_us>=source['until_us']:reject('interval_not_ready')
   values=[]
   for l in self._lines(job,generation):
    ready=not l['error'] and at_us<min(l['covered'],source['until_us']);args=(job,generation,l['line_id'],l['geometry_revision'],at_us)
    total=s.db.execute('SELECT count(*) FROM p_count_lines_events WHERE job=? AND generation=? AND line_id=? AND geometry_revision=? AND time_us<=?',args).fetchone()[0] if ready else None
    following=s.db.execute('SELECT min(time_us) FROM p_count_lines_events WHERE job=? AND generation=? AND line_id=? AND geometry_revision=? AND time_us>?',args).fetchone()[0] if ready else None
    until=min(l['covered'],source['until_us'],following if following is not None else source['until_us']) if ready else at_us
    scope='partial' if source['analysis']=='partial_failed' else 'final' if source['analysis']=='complete' and l['covered']>=source['until_us'] else 'building'
    values.append(dict(line_id=l['line_id'],geometry_revision=l['geometry_revision'],status='unavailable' if l['error'] else 'ready' if ready else 'pending',result_scope=scope,covered_until_us=l['covered'],valid_until_us=until,total=total,error_code=l['error']))
   return dict(job_id=job,generation=generation,**PROTOCOL,revision=revision,at_us=at_us,available_until_us=source['until_us'],analysis_state=source['analysis'],lines=values,expires_at=source['expires'])
 def reduce(self,job):return self.reducer.reduce(job)
