from tests.contract.test_video_inspections import seed
from tests.fixtures_011 import line
def test_explicit_import_routes(client,auth_headers,tmp_path):
 s,state=seed(client,tmp_path);g=state['generation'];root='/api/v1/video-jobs/temporal/playback';body=dict(generation=g,expected_revision=0)
 assert client.post(root+'/count-lines/import-legacy',json=body,headers=auth_headers).status_code==409
 assert client.put(root+'/directed-count',json={**body,'line':line()['segment'],'direction':'positive_to_negative'},headers=auth_headers).status_code==200
 first=client.post(root+'/count-lines/import-legacy',json=body,headers=auth_headers);assert first.status_code==200 and first.json()['lines'][0]['origin']=='legacy_import'
 assert client.post(root+'/count-lines/import-legacy',json=body,headers=auth_headers).json()==first.json()
 assert client.get(root+'/directed-count?generation='+g+'&at_us=0',headers=auth_headers).json()['direction']=='positive_to_negative'
