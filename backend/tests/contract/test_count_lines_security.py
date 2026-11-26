import json
from pathlib import Path
from uuid import uuid4
from tests.contract.test_video_inspections import seed
from tests.fixtures_011 import line
from app.domain.count_lines import Collection,CountSnapshot
def test_routes_closed_readonly_and_permissions(client,auth_headers,tmp_path):
 store,state=seed(client,tmp_path);g=state['generation'];url='/api/v1/video-jobs/temporal/playback/count-lines'
 before=store.db.total_changes
 descriptor=client.get(url+'?generation='+g,headers=auth_headers);assert descriptor.status_code==200;Collection.model_validate(descriptor.json())
 # Background inventory can write independently; reads must not create count rows.
 assert store.db.execute('SELECT count(*) FROM p_count_lines_collection').fetchone()[0]==0
 assert client.get(url+'?generation='+g).status_code==401
 for suffix in ['&extra=1','&generation='+g]:assert client.get(url+'?generation='+g+suffix,headers=auth_headers).status_code==422
 assert client.get(url+'?generation='+str(uuid4()),headers=auth_headers).status_code==409
 body=dict(generation=g,expected_revision=0,lines=[line()]);resp=client.put(url,json=body,headers=auth_headers);assert resp.status_code==200;Collection.model_validate(resp.json());assert resp.headers['cache-control']=='no-store'
 for patch in [dict(expected_revision=True),dict(expected_revision=2**53),dict(direction='both')]:assert client.put(url,json={**body,**patch},headers=auth_headers).status_code==422
 for at in ['true','-1','9007199254740992','1.0']:
  assert client.get(url+'/counts?generation='+g+'&revision=1&at_us='+at,headers=auth_headers).status_code==422
 response=client.get(url+'/counts?generation='+g+'&revision=1&at_us=0',headers=auth_headers);assert response.status_code==200;CountSnapshot.model_validate(response.json())
 assert client.put(url,content=b' '*65537,headers={**auth_headers,'Content-Type':'application/json'}).status_code==413
 # Request DTOs remain separate from the legacy directional contract.
 assert client.put('/api/v1/video-jobs/temporal/playback/directed-count',json={**body,'line':body['lines'][0]['segment']},headers=auth_headers).status_code==422
def test_semantic_conflicts(client,auth_headers,tmp_path):
 _,state=seed(client,tmp_path);examples=json.loads((Path(__file__).resolve().parents[3]/'specs/011-video-multilinea-velocidad/contracts/examples.json').read_text(encoding='utf-8'))
 url='/api/v1/video-jobs/temporal/playback/count-lines'
 for e in examples['invalid_semantic']:
  if e['name'] in ['duplicate_normalized_name','duplicate_color_case']:
   assert client.put(url,json={**e['data'],'generation':state['generation']},headers=auth_headers).status_code==409
