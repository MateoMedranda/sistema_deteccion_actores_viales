import pytest
from starlette.datastructures import QueryParams
from app.web.proxy import classify,RelayError
GEN='11111111-1111-4111-8111-111111111111';IID='22222222-2222-4222-8222-222222222222';ASSET='33333333-3333-4333-8333-333333333333'
@pytest.mark.parametrize('method,suffix,query',[
 ('GET','capabilities',''),('POST','inspections',''),('GET','inspections/'+IID,''),
 ('GET','inspections/'+IID+'/assets/'+ASSET+'/vehicle',''),('GET','inspections/'+IID+'/plate-preview','profile=display-contrast-v1'),
 ('PUT','directed-count',''),('GET','directed-count','generation='+GEN+'&at_us=0'),('DELETE','directed-count','generation='+GEN+'&expected_revision=0'),
 ('GET','detection-summary','generation='+GEN),('GET','export','renderer=vehicle-labels-v1'),('POST','export','renderer=vehicle-labels-v1'),('GET','export/content','renderer=vehicle-labels-v1'),('HEAD','export/content','renderer=vehicle-labels-v1'),
])
def test_all_thirteen_additive_operations_are_allowlisted_and_closed(method,suffix,query):
 path='/api/v1/video-jobs/test/playback/'+suffix
 assert classify(method,path,path.encode(),QueryParams(query))
 with pytest.raises(RelayError):classify(method,path,path.encode(),QueryParams(query+('&' if query else '')+'unknown=1'))

def test_legacy_routes_do_not_require_new_selectors(enrichment_client,auth_headers,tmp_path):
 from tests.integration.test_video_profile_pipeline import submit,report
 client=enrichment_client;job=submit(client,tmp_path,auth_headers);report(client,job)
 export=client.get(f'/api/v1/video-jobs/{job}/playback/export',headers=auth_headers)
 assert export.status_code==200 and 'renderer_version' not in export.json()
 response=client.get(f'/api/v1/video-jobs/{job}/playback/count?at_us=0',headers=auth_headers)
 assert response.status_code==200
 result=response.json();assert 'a_to_b' in result and 'b_to_a' in result and 'policy_version' not in result
 assert client.get(f'/api/v1/video-jobs/{job}/summary',headers=auth_headers).status_code==200


def test_new_json_routes_preserve_gateway_csrf_and_credentials():
 from tests.integration.test_web_gateway_security import fixture,bootstrap
 from fastapi.testclient import TestClient
 app,calls,key=fixture()
 with TestClient(app,base_url='http://127.0.0.1:4173') as client:
  headers=bootstrap(client);before=len(calls)
  response=client.post('/web-api/api/v1/video-jobs/test/playback/inspections',headers={**headers,'X-UI-CSRF':'bad'},json={})
  assert response.status_code==403 and len(calls)==before
  response=client.post('/web-api/api/v1/video-jobs/test/playback/inspections',headers=headers,json={})
  assert response.status_code==200 and len(calls)==before+1 and key not in response.text
  assert client.get('/web-api/api/v1/video-jobs/test/playback/capabilities',headers={**headers,'Origin':'http://evil.invalid','Sec-Fetch-Site':'cross-site'}).status_code==403
