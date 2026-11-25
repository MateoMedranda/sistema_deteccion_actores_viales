import time,json
from datetime import datetime,UTC
from app.api.error_handlers import ApiError
from tests.contract.test_video_inspections import seed
from tests.fixtures_010 import frame,observation

def test_all_new_derivatives_retire_with_parent(client,auth_headers,tmp_path):
 store,state=seed(client,tmp_path);owner='default';service=client.app.state.video_inspections;service.close()
 result=service.admit('temporal',owner,dict(generation=state['generation'],track_id=1,frame_index=30))
 counter=client.app.state.directed_count;counter.configure('temporal',owner,dict(generation=state['generation'],expected_revision=0,line=dict(point_a=dict(x=.1,y=.5),point_b=dict(x=.9,y=.5)),direction='negative_to_positive'));counter.reduce('temporal')
 assert store.db.execute('SELECT count(*) FROM p_detection_tracks WHERE job=?',('temporal',)).fetchone()[0]==1
 store.withdraw('temporal',owner)
 for table in ['p_video_inspections','p_directed_count_state','p_directed_count_events','p_directed_count_tracks','p_detection_inventory','p_detection_tracks','p_detection_votes','p_video_label_exports']:
  assert store.db.execute('SELECT count(*) FROM '+table+' WHERE job=?',('temporal',)).fetchone()[0]==0,table
 assert client.get('/api/v1/video-jobs/temporal/playback/inspections/'+result['inspection_id'],headers=auth_headers).status_code==410

def test_crossing_class_snapshot_and_restart_cas_survive_inventory_changes(client,auth_headers,tmp_path):
 from app.services.directed_count_service import DirectedCountService
 store,state=seed(client,tmp_path);service=client.app.state.directed_count
 body=dict(generation=state['generation'],expected_revision=0,line=dict(point_a=dict(x=.1,y=.5),point_b=dict(x=.9,y=.5)),direction='negative_to_positive');service.configure('temporal','default',body)
 store.publish('temporal',[frame(201,[observation(x=50,y=60,cls='truck')])]);service.reduce('temporal');service.reduce('temporal')
 event=dict(store.db.execute("SELECT * FROM p_directed_count_events WHERE job='temporal'").fetchone());assert event['class_key_at_crossing']=='truck'
 store.publish('temporal',[frame(i,[observation(x=50,y=70,cls='car')]) for i in range(202,207)])
 restored=DirectedCountService(store);restored.reduce('temporal')
 assert dict(store.db.execute("SELECT * FROM p_directed_count_events WHERE job='temporal'").fetchone())==event
 assert restored.snapshot('temporal','default',state['generation'],20_100_000)['total']==1

def test_control_body_cap_and_strict_query(client,auth_headers,tmp_path):
 store,state=seed(client,tmp_path);url='/api/v1/video-jobs/temporal/playback'
 response=client.post(url+'/inspections',headers={**auth_headers,'Content-Type':'application/json'},content=b' '*65537);assert response.status_code==413
 response=client.get(url+'/directed-count?generation='+state['generation']+'&at_us=1.0',headers=auth_headers);assert response.status_code==422
 response=client.get(url+'/capabilities',headers=auth_headers);assert response.status_code==200 and len(response.content)<=1024**2 and response.headers['cache-control']=='no-store'


def test_each_new_resource_preserves_owner_isolation(client,auth_headers,tmp_path):
 store,state=seed(client,tmp_path);client.app.state.settings.api_keys='other:other-key'
 paths=['/capabilities','/detection-summary?generation='+state['generation'],'/directed-count?generation='+state['generation']+'&at_us=0','/export?renderer=vehicle-labels-v1']
 for suffix in paths:
  response=client.get('/api/v1/video-jobs/temporal/playback'+suffix,headers={'X-API-Key':'other-key'})
  assert response.status_code==404 and len(response.content)<1048576
 response=client.post('/api/v1/video-jobs/temporal/playback/inspections',headers={'X-API-Key':'other-key'},json=dict(generation=state['generation'],track_id=1,frame_index=0))
 assert response.status_code==404


def test_processing_restart_fails_once_without_repeating_models(client,auth_headers,tmp_path):
 from app.services.video_inspection_store import InspectionStore
 store,state=seed(client,tmp_path);service=client.app.state.video_inspections;service.close()
 value=service.admit('temporal','default',dict(generation=state['generation'],track_id=1,frame_index=30));value.update(state='processing',result_revision=5)
 with store.lock,store.db:store.db.execute("UPDATE p_video_inspections SET state='processing',payload=? WHERE id=?",(json.dumps(value),value['inspection_id']))
 restored=InspectionStore(store,service.settings);result=restored.get('temporal','default',value['inspection_id'])
 assert result['state']=='failed' and result['error_code']=='inspection_interrupted' and result['result_revision']==6
