from tests.contract.test_video_inspections import seed,schema_check
def test_readonly_summary_generation_and_zero(client,auth_headers,tmp_path):
 store,state=seed(client,tmp_path);url='/api/v1/video-jobs/temporal/playback/detection-summary?generation='+state['generation']
 before=store.db.total_changes;response=client.get(url,headers=auth_headers);assert response.status_code==200
 schema_check('DetectionSummary',response.json());assert response.json()['total_tracks']==1
 assert store.db.total_changes==before
 assert client.get(url+'&unknown=1',headers=auth_headers).status_code==422
 assert client.get(url.replace(state['generation'],'11111111-1111-4111-8111-111111111111'),headers=auth_headers).status_code==409
