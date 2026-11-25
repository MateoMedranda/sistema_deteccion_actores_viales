import json
from pathlib import Path
import cv2,numpy as np
from app.api.error_handlers import ApiError
from app.services.plate_profiles import display_contrast,NotApplicable

def preview(service,job,owner,iid,profile):
 if profile!='display-contrast-v1':raise ApiError(422,'profile_invalid','Invalid profile.')
 with service.store.lock,service.store.db:
  rec=service.get_record(job,owner,iid);value=json.loads(rec['payload']);paths=json.loads(rec['paths'])
  if not value['plate_asset']:raise ApiError(404,'inspection_asset_unavailable','No plate crop.')
  image=cv2.imdecode(np.frombuffer(Path(paths['plate']).read_bytes(),np.uint8),cv2.IMREAD_COLOR)
  h,w=image.shape[:2]
  try:png,(ow,oh),scale,_=display_contrast(image)
  except NotApplicable:raise ApiError(409,'preview_not_applicable','The visual profile is unavailable.')
  metadata=dict(version='inspection-plate-preview-v1',inspection_id=iid,plate_asset_id=value['plate_asset']['asset_id'],job_id=job,generation=value['generation'],track_id=value['track_id'],frame_index=value['frame_index'],time_us=value['time_us'],coordinate_space='plate-crop',original_width=w,original_height=h,processed_width=ow,processed_height=oh,source_to_processed=[scale,0,0,scale,0,0],profile_id=profile,policy_version='display-contrast-v1',display_only=True,expires_at=value['expires_at'])
  return png,metadata
