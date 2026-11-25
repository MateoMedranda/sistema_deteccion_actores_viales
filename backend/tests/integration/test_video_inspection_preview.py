import json,time
import numpy as np
from PIL import Image
from tests.contract.test_video_inspections import seed,schema_check
def test_preview_cache_is_bounded_contextual_and_does_not_repeat_ocr(enrichment_client,auth_headers,tmp_path,monkeypatch):
 client=enrichment_client;store,state=seed(client,tmp_path);service=client.app.state.video_inspections
 def extractor(source,pts,num,den,box,output,**kwargs):
  Image.fromarray(np.arange(300,dtype=np.uint8).reshape(10,10,3)).save(output,format='PNG');return output
 monkeypatch.setattr('app.services.video_inspections.extract_frame',extractor)
 url='/api/v1/video-jobs/temporal/playback/inspections';first=client.post(url,json=dict(generation=state['generation'],track_id=1,frame_index=200),headers=auth_headers).json()
 for _ in range(100):
  result=client.get(url+'/'+first['inspection_id'],headers=auth_headers).json()
  if result['state'] in ['ready','partial']:break
  time.sleep(.03)
 assert result['plate_asset']
 from app.services.plate_profiles import display_contrast
 calls=[]
 def observed(image):calls.append(1);return display_contrast(image)
 monkeypatch.setattr('app.services.video_inspection_preview.display_contrast',observed)
 preview=result['plate_preview_url']+'?profile=display-contrast-v1'
 first=client.get(preview,headers=auth_headers);second=client.get(preview,headers=auth_headers)
 assert first.status_code==second.status_code==200 and first.content==second.content and calls==[1]
 schema_check('InspectionPlatePreviewMetadata',json.loads(first.headers['x-plate-preview-metadata']))
 rec=store.db.execute('SELECT * FROM p_video_inspections WHERE id=?',(result['inspection_id'],)).fetchone()
 assert 'preview' in json.loads(rec['paths']) and rec['bytes']<=service.settings.video_inspection_max_bytes_per_job
 from pathlib import Path
 assert rec['bytes']==sum(Path(path).stat().st_size for path in json.loads(rec['paths']).values())
 store.withdraw('temporal','default');assert not any(service.directory.iterdir())
