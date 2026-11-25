"""One bounded worker; exact frozen crops, existing processors and parent authority."""
import json,logging,threading,time
from pathlib import Path
from uuid import uuid4
from datetime import datetime
import cv2,numpy as np
from app.api.error_handlers import ApiError
from app.services.video_inspection_store import InspectionStore
from app.services.video_detail_access import parent,reader_lease
from app.services.video_progressive_store import dump,now
from app.domain.vehicle_taxonomy import is_vehicle
from app.adapters.selected_frame_extractor import extract_frame

class VideoInspections(InspectionStore):
 def __init__(self,store,settings,processor,slots):
  super().__init__(store,settings);self.processor,self.slots=processor,slots;self.preview_slot=threading.BoundedSemaphore(1)
  self.stop=threading.Event();self.thread=threading.Thread(target=self.run,name='video-inspection',daemon=True)
  self.logger=logging.getLogger('road_actor_detection')
 def start(self):self.thread.start()
 def close(self):
  self.stop.set()
  if self.thread.is_alive():self.thread.join()
 def resource(self,job,owner,iid,asset,kind):
  with self.store.lock:
   rec=self.get_record(job,owner,iid);value=json.loads(rec['payload']);entry=value['vehicle' if kind=='vehicle' else 'plate_asset']
   if not entry or entry['asset_id']!=asset:raise ApiError(404,'inspection_asset_unavailable','The crop is unavailable.')
   return Path(json.loads(rec['paths'])[kind])
 def run(self):
  while not self.stop.wait(.05):
   rec=None
   with self.store.lock,self.store.db:
    row=self.store.db.execute("SELECT i.* FROM p_video_inspections i JOIN p_video v ON i.job=v.job WHERE i.state='queued' AND i.expires>? AND v.retired=0 AND v.expires>? ORDER BY i.rowid LIMIT 1",(now().isoformat(),now().isoformat())).fetchone()
    if row:rec=dict(row);self.store.db.execute("UPDATE p_video_inspections SET state='preparing' WHERE id=?",(rec['id'],))
   if rec:self.evaluate(rec)
 def evaluate(self,rec):
  started=time.monotonic();s=self.store;iid=rec['id'];job=rec['job'];value=json.loads(rec['payload']);paths={};created=[]
  def active():
   if self.stop.is_set() or datetime.fromisoformat(rec['expires'])<=now():return False
   try:
    with s.lock:parent(s,job,owner,rec['generation'])
    return True
   except ApiError:return False
  def publish(state):
   if not active():raise RuntimeError('inspection_interrupted')
   value['state']=state;value['result_revision']+=1
   with s.lock,s.db:
    self.get_record(job,owner,iid)
    actual=rec['bytes'] if state in ['queued','preparing','processing'] else sum(Path(p).stat().st_size for p in paths.values())
    s.db.execute('UPDATE p_video_inspections SET state=?,payload=?,paths=?,bytes=? WHERE id=?',(state,dump(value),dump(paths),actual,iid))
  def asset(kind,data):
   if len(data)>self.settings.video_inspection_max_resource_bytes:raise ValueError('inspection_resource_limit')
   aid=str(uuid4());path=self.directory/(aid+'.png');temporary=path.with_suffix('.tmp');created.extend([temporary,path]);temporary.write_bytes(data)
   if not active():raise RuntimeError('inspection_interrupted')
   temporary.replace(path);paths[kind]=str(path)
   return dict(asset_id=aid,kind=kind,url=f'/api/v1/video-jobs/{job}/playback/inspections/{iid}/assets/{aid}/{kind}',expires_at=rec['expires'])
  try:
   with s.lock:
    row=s.row(job);owner=row['owner'];timeline=json.loads(row['timeline']);source=Path(row['source'])
    receipt=json.loads(s.db.execute('SELECT payload FROM p_frames WHERE job=? AND idx=?',(job,rec['idx'])).fetchone()[0])
   # The private receipt stores each frame's rational time base for exact PTS comparison.
   num=receipt.get('time_base_num',timeline['time_base_num']);den=receipt.get('time_base_den',timeline['time_base_den'])
   temporary=self.directory/(iid+'.extract.tmp');created.append(temporary)
   with reader_lease(s,job,owner,source):extract_frame(source,int(receipt['pts']),num,den,value['bbox'],temporary,timeout=self.settings.video_inspection_decode_timeout_seconds,max_frames=self.settings.video_inspection_decode_max_frames,max_bytes=self.settings.video_inspection_max_resource_bytes,active=active)
   value['vehicle']=asset('vehicle',temporary.read_bytes());temporary.unlink(missing_ok=True)
   publish('processing')
   if not is_vehicle(value['class_name']) or not self.processor.usable:
    value['attributes'].update(status='not_applicable');value['plate'].update(status='not_applicable');publish('not_applicable')
   else:
    image=cv2.imdecode(np.frombuffer(Path(paths['vehicle']).read_bytes(),np.uint8),cv2.IMREAD_COLOR)
    with self.slots:
     if not active():raise RuntimeError('inspection_interrupted')
     attrs,plate=self.processor.enrich(image,rec['idx'],job_id=job,source_type='video',should_continue=active)
    value['attributes']=dict(status=attrs['status'],items=[dict(name=a['name'],value=a.get('label',a.get('value','')),confidence=a['confidence'],inspection_id=iid) for a in attrs.get('items',[])[:20]],error_code=attrs.get('error_code'))
    value['plate']={**value['plate'],**{k:plate[k] for k in ['status','text','ocr_confidence','used_enhancement','error_code'] if k in plate}}
    if plate.get('bbox_relative'):
     b=plate['bbox_relative'];h,w=image.shape[:2];x1,y1,x2,y2=[round(b[k]*size) for k,size in zip(['x_min','y_min','x_max','y_max'],[w,h,w,h])]
     crop=image[max(0,y1):min(h,y2),max(0,x1):min(w,x2)];ok,png=cv2.imencode('.png',crop)
     if ok:
      value['plate_asset']=asset('plate',png.tobytes());value['plate_preview_url']=f'/api/v1/video-jobs/{job}/playback/inspections/{iid}/plate-preview';value['plate_preview_profiles']=['display-contrast-v1']
    publish('partial' if attrs['status']=='failed' or plate['status']=='failed' else 'ready')
  except Exception as exc:
   if 'owner' in locals():
    try:
     value['error_code']='inspection_decode_timeout' if isinstance(exc,TimeoutError) else 'inspection_frame_unavailable' if isinstance(exc,ValueError) else 'inspection_interrupted';publish('unavailable' if isinstance(exc,(ValueError,TimeoutError)) else 'failed')
    except Exception:pass
   for path in created:
    if str(path) not in paths.values():path.unlink(missing_ok=True)
   self.logger.warning('video_inspection_failed',extra={'job_id':job,'error_code':value.get('error_code'),'exception_type':type(exc).__name__})
  finally:
   if not ('owner' in locals() and active()):
    for path in created:path.unlink(missing_ok=True)
   self.logger.info('video_inspection_outcome',extra={'job_id':job,'elapsed_ms':round((time.monotonic()-started)*1000),'status':value['state']})
