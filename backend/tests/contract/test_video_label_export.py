from tests.integration.test_video_profile_pipeline import submit,report
from tests.contract.test_video_inspections import schema_check
def test_label_variant_is_distinct_and_closed(enrichment_client,tmp_path,auth_headers,monkeypatch):
 client=enrichment_client;job=submit(client,tmp_path,auth_headers);report(client,job);exporter=client.app.state.progressive_export;monkeypatch.setattr(exporter,'claim',lambda:None)
 url=f'/api/v1/video-jobs/{job}/playback/export'
 assert 'renderer_version' not in client.get(url,headers=auth_headers).json()
 result=client.get(url+'?renderer=vehicle-labels-v1',headers=auth_headers);assert result.status_code==200;schema_check('LabelExportStatus',result.json());assert result.json()['state']=='waiting'
 assert client.get(url+'?renderer=bad',headers=auth_headers).status_code==422
 assert client.post(url+'?renderer=vehicle-labels-v1',headers=auth_headers,json={}).status_code==422
 for _ in range(2):assert client.post(url+'?renderer=vehicle-labels-v1',headers=auth_headers).json()['state']=='queued'
 assert client.get(url,headers=auth_headers).json()['state']=='waiting'
 assert client.get(url+'/content?renderer=vehicle-labels-v1',headers=auth_headers).status_code==409
