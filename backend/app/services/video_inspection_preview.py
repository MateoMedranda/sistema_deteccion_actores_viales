"""One deterministic visual derivative per immutable plate; no OCR and no model slot."""
import json
from pathlib import Path
from uuid import uuid4
from PIL import Image
import cv2,numpy as np
from app.api.error_handlers import ApiError
from app.services.plate_profiles import display_contrast,NotApplicable
from app.services.video_detail_access import reader_lease
from app.services.video_progressive_store import dump

def preview(service,job,owner,iid,profile):
 if profile!='display-contrast-v1':raise ApiError(422,'profile_invalid','Invalid profile.')
 if not service.preview_slot.acquire(blocking=False):raise ApiError(429,'preview_busy','Visual preview capacity reached.')
 temporary=None
 try:
  s=service.store
  with s.lock:
   rec=service.get_record(job,owner,iid);value=json.loads(rec['payload']);paths=json.loads(rec['paths'])
   if not value['plate_asset']:raise ApiError(404,'inspection_asset_unavailable','No plate crop.')
   original=Path(paths['plate']);cached=Path(paths['preview']) if paths.get('preview') else None
  with reader_lease(s,job,owner,original):
   with Image.open(original) as header:w,h=header.size
   if w*h>2_000_000:raise ApiError(409,'preview_not_applicable','Visual profile exceeds its pixel limit.')
   if cached and cached.is_file():
    with reader_lease(s,job,owner,cached):
     png=cached.read_bytes()
     with Image.open(cached) as header:ow,oh=header.size
    scale=ow/w
   else:
    image=cv2.imdecode(np.frombuffer(original.read_bytes(),np.uint8),cv2.IMREAD_COLOR)
    try:png,(ow,oh),scale,_=display_contrast(image)
    except NotApplicable:raise ApiError(409,'preview_not_applicable','The visual profile is unavailable.')
    destination=service.directory/(value['plate_asset']['asset_id']+'.display.png');temporary=service.directory/(str(uuid4())+'.tmp');temporary.write_bytes(png)
    with s.lock,s.db:
     current=service.get_record(job,owner,iid);paths=json.loads(current['paths'])
     used=s.db.execute('SELECT coalesce(sum(bytes),0) FROM p_video_inspections WHERE job=?',(job,)).fetchone()[0]
     if used+len(png)>service.settings.video_inspection_max_bytes_per_job:raise ApiError(429,'inspection_quota','Visual preview capacity reached.')
     temporary.replace(destination);paths['preview']=str(destination)
     s.db.execute('UPDATE p_video_inspections SET paths=?,bytes=bytes+? WHERE id=?',(dump(paths),len(png),iid))
  with s.lock:service.get_record(job,owner,iid)
  metadata=dict(version='inspection-plate-preview-v1',inspection_id=iid,plate_asset_id=value['plate_asset']['asset_id'],job_id=job,generation=value['generation'],track_id=value['track_id'],frame_index=value['frame_index'],time_us=value['time_us'],coordinate_space='plate-crop',original_width=w,original_height=h,processed_width=ow,processed_height=oh,source_to_processed=[scale,0,0,scale,0,0],profile_id=profile,policy_version='display-contrast-v1',display_only=True,expires_at=value['expires_at'])
  return png,metadata
 finally:
  if temporary:temporary.unlink(missing_ok=True)
  service.preview_slot.release()
