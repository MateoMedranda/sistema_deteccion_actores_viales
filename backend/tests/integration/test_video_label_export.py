import time,av
from tests.integration.test_video_profile_pipeline import submit,report
def test_real_mp4_variant_range_and_model_free_export(enrichment_client,tmp_path,auth_headers,monkeypatch):
 from tests.fixtures_progressive import video
 monkeypatch.setattr('tests.integration.test_video_profile_pipeline.video',lambda path:video(path,width=640,height=360))
 client=enrichment_client;job=submit(client,tmp_path,auth_headers);report(client,job);exporter=client.app.state.progressive_export
 def forbidden(*a,**k):raise AssertionError('No models while exporting')
 monkeypatch.setattr(client.app.state.video_worker.processor.detector,'detect',forbidden)
 monkeypatch.setattr(client.app.state.progressive_worker.processor,'enrich',forbidden)
 # The 64px source cannot contain 10 legible labels: use a sparse persisted test observation.
 store=exporter.store
 import json
 with store.lock,store.db:
  for row in store.db.execute('SELECT idx,payload FROM p_frames WHERE job=?',(job,)).fetchall():
   f=json.loads(row['payload']);f['observations']=f['observations'][:1];store.db.execute('UPDATE p_frames SET payload=? WHERE job=? AND idx=?',(json.dumps(f),job,row['idx']))
 url=f'/api/v1/video-jobs/{job}/playback/export?renderer=vehicle-labels-v1'
 assert client.post(url,headers=auth_headers).status_code==202
 end=time.monotonic()+15
 while time.monotonic()<end:
  result=client.get(url,headers=auth_headers).json()
  if result['state'] in ['ready','failed']:break
  time.sleep(.05)
 assert result['state']=='ready',result
 content=client.get(result['url'],headers={**auth_headers,'Range':'bytes=0-31'});assert content.status_code==206
 assert client.head(result['url'],headers=auth_headers).status_code==200
 path=exporter.variants.path(job,'default','vehicle-labels-v1')
 with av.open(str(path)) as c:frames=list(c.decode(video=0));assert len(frames)==12 and c.streams.video[0].codec_context.name=='h264'
 assert client.app.state.video_jobs.get(job,'default').output_path is None
 assert client.get(f'/api/v1/video-jobs/{job}/playback/export',headers=auth_headers).json()['state']=='waiting'
