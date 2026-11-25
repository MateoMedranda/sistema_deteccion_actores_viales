from tests.contract.test_video_inspections import seed,schema_check
def test_directed_route_query_and_generation(client,auth_headers,tmp_path):
 store,state=seed(client,tmp_path);url='/api/v1/video-jobs/temporal/playback/directed-count'
 body=dict(generation=state['generation'],expected_revision=0,line=dict(point_a=dict(x=.1,y=.5),point_b=dict(x=.9,y=.5)),direction='negative_to_positive')
 response=client.put(url,json=body,headers=auth_headers);assert response.status_code==200;schema_check('DirectedCount',response.json())
 assert client.put(url,json=body,headers=auth_headers).status_code==409
 assert client.get(url+'?generation='+state['generation']+'&at_us=0&at_us=1',headers=auth_headers).status_code==422
 assert client.get(url+'?generation='+state['generation']+'&at_us=true',headers=auth_headers).status_code==422
 assert client.delete(url+'?generation='+state['generation']+'&expected_revision=1',headers=auth_headers).status_code==204
