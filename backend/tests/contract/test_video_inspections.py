import json,time
from datetime import datetime,timedelta,timezone
from tests.fixtures_010 import frame,observation
from jsonschema import Draft202012Validator,FormatChecker
from pathlib import Path

def schema_check(name,value):
 schema=json.loads((Path(__file__).resolve().parents[3]/'specs/010-video-detalle-conteo/contracts/schemas.json').read_text())
 Draft202012Validator({**schema,'$ref':'#/$defs/'+name},format_checker=FormatChecker()).validate(value)

def seed(client,tmp_path):
 store=client.app.state.progressive_store
 source=tmp_path/'source.mp4';source.write_bytes(b'fixture')
 state=store.create('temporal','default',source,dict(width=100,height=100,duration=30),datetime.now(timezone.utc)+timedelta(hours=1),True)
 store.publish('temporal',[frame(i,[observation(x=20 if i<200 else 60)]) for i in range(201)])
 return store,state

def test_inspection_dedup_context_authority_and_closed_requests(client,auth_headers,tmp_path):
 store,state=seed(client,tmp_path);url='/api/v1/video-jobs/temporal/playback/inspections'
 body=dict(generation=state['generation'],track_id=1,frame_index=30)
 response=client.post(url,json=body,headers=auth_headers);assert response.status_code==202
 first=response.json();schema_check('Inspection',first)
 assert client.post(url,json=body,headers=auth_headers).json()['inspection_id']==first['inspection_id']
 assert client.post(url,json={**body,'frame_index':200},headers=auth_headers).json()['inspection_id']!=first['inspection_id']
 assert first['time_us']==3_000_000 and first['bbox']['x_min']==15
 for patch in ({'frame_index':True},{'bbox':{}},{'track_id':9},{'frame_index':999},{'generation':'11111111-1111-4111-8111-111111111111'}):
  assert client.post(url,json={**body,**patch},headers=auth_headers).status_code in [404,409,422]
 assert client.get(url+'/'+first['inspection_id']+'?foo=1',headers=auth_headers).status_code==422
 assert client.get(url+'/'+first['inspection_id'],headers={'X-API-Key':'bad'}).status_code==401

def test_local_expiry_does_not_retire_parent(client,auth_headers,tmp_path):
 store,state=seed(client,tmp_path);url='/api/v1/video-jobs/temporal/playback/inspections';body=dict(generation=state['generation'],track_id=1,frame_index=30)
 result=client.post(url,json=body,headers=auth_headers).json();iid=result['inspection_id']
 with store.lock,store.db:store.db.execute('UPDATE p_video_inspections SET expires=? WHERE id=?',('2000-01-01T00:00:00+00:00',iid))
 assert client.post(url,json=body,headers=auth_headers).status_code==410
 assert client.get(url+'/'+iid,headers=auth_headers).status_code==410
 assert client.get('/api/v1/video-jobs/temporal/playback',headers=auth_headers).status_code==200
