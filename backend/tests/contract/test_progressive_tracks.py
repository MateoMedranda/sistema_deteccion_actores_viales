from datetime import UTC,datetime,timedelta
from types import SimpleNamespace
def test_pending_track_is_readable_and_foreign_owner_is_not(client,tmp_path,auth_headers):
 store=client.app.state.progressive_store;evidence=client.app.state.progressive_evidence
 path=tmp_path/"source";path.write_bytes(b"original")
 store.create("pending-job","default",path,dict(width=64,height=48,fps=10,duration=1),datetime.now(UTC)+timedelta(minutes=5))
 ob=dict(track_id=7,class_id=0,class_name="car",confidence=.9,raw_bbox=dict(x_min=1,y_min=1,x_max=20,y_max=20),display_bbox=None)
 frames=[dict(frame_index=0,start_us=0,end_us=100000,pts="0",observations=[ob])]
 store.publish("pending-job",frames,on_publish=lambda:evidence.commit(SimpleNamespace(job_id="pending-job"),[],frames))
 url="/api/v1/video-jobs/pending-job/playback/tracks/7"
 result=client.get(url,headers=auth_headers)
 assert result.status_code==200,result.text
 assert result.json()["attributes"]["status"]=="pending"
 assert result.json()["final"] is False
 client.app.state.settings.api_keys="foreign:another"
 assert client.get(url,headers={"X-API-Key":"another"}).status_code==404
