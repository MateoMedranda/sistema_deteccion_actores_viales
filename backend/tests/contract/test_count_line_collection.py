from tests.contract.test_video_inspections import seed
def test_empty_descriptor_creates_no_state(client,auth_headers,tmp_path):
 s,state=seed(client,tmp_path);url='/api/v1/video-jobs/temporal/playback/count-lines?generation='+state['generation']
 before=s.db.total_changes;response=client.get(url,headers=auth_headers);assert response.status_code==200
 assert response.json()['revision']==0 and response.json()['lines']==[] and response.json()['admitted_count']==0
 assert s.db.total_changes==before
