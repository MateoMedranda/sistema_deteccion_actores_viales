from tests.contract.test_video_inspections import seed,schema_check
from pathlib import Path
from PIL import Image
import time

def test_worker_uses_selected_context_and_stable_assets(client,auth_headers,tmp_path,monkeypatch):
 store,state=seed(client,tmp_path);service=client.app.state.video_inspections
 def extractor(source,pts,num,den,box,output,**kwargs):
  Image.new('RGB',(box['x_max']-box['x_min'],10),(int(pts)%255,50,50)).save(output,format="PNG");return output
 monkeypatch.setattr('app.services.video_inspections.extract_frame',extractor)
 url='/api/v1/video-jobs/temporal/playback/inspections'
 first=client.post(url,json=dict(generation=state['generation'],track_id=1,frame_index=200),headers=auth_headers).json()
 for _ in range(100):
  result=client.get(url+'/'+first['inspection_id'],headers=auth_headers).json()
  if result['state'] not in ['queued','preparing','processing']:break
  time.sleep(.03)
 schema_check('Inspection',result);assert result['vehicle'] and result['time_us']==20_000_000
 asset=result['vehicle'];response=client.get(asset['url'],headers=auth_headers)
 assert response.status_code==200 and response.headers['cache-control']=='no-store'
 assert client.get(url+'/'+first['inspection_id'],headers=auth_headers).json()['vehicle']==asset
 service.cleanup();assert store.row('temporal')['retired']==0


def test_admission_limits_restart_and_tombstone_retention(client,auth_headers,tmp_path):
 store,state=seed(client,tmp_path);service=client.app.state.video_inspections
 service.close()
 service.settings.video_inspection_max_contexts_per_job=1
 body=dict(generation=state['generation'],track_id=1,frame_index=0)
 first=service.admit('temporal','default',body)
 from app.api.error_handlers import ApiError
 import pytest
 with pytest.raises(ApiError) as error:service.admit('temporal','default',{**body,'frame_index':1})
 assert error.value.status_code==429
 with store.lock,store.db:store.db.execute("UPDATE p_video_inspections SET expires='2000-01-01T00:00:00+00:00' WHERE id=?",(first['inspection_id'],))
 service.cleanup()
 assert store.db.execute('SELECT count(*) FROM p_video_inspections').fetchone()[0]==1
 with pytest.raises(ApiError):service.admit('temporal','default',body)
 store.withdraw('temporal','default')
 assert store.db.execute('SELECT count(*) FROM p_video_inspections').fetchone()[0]==0
