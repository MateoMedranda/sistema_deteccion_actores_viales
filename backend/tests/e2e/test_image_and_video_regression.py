import time
from tests.video_fixtures import FakeProbe,make_h264_mp4
from tests.image_exploration_fixtures import scene_bytes

def test_image_health_regression(client):
    assert client.get("/health/live").status_code==200
    assert client.get("/health/ready").status_code==200

def test_image_video_and_enrichment_contracts_together(enrichment_client,auth_headers,tmp_path):
    client=enrichment_client
    image=client.post("/api/v1/detections/images",headers=auth_headers,files={"image":("scene.jpg",scene_bytes(),"image/jpeg")})
    assert image.status_code==200
    assert client.get(image.json()["original_image"]["url"],headers=auth_headers).status_code==200
    client.app.state.video_job_service.probe=FakeProbe()
    media=make_h264_mp4(tmp_path/"controlled.mp4")
    with media.open("rb") as stream:
        response=client.post("/api/v1/video-jobs",headers=auth_headers,files={"video":("controlled.mp4",stream,"video/mp4")})
    assert response.status_code==202
    video_id=response.json()["job_id"]
    deadline=time.monotonic()+10
    while time.monotonic()<deadline:
        state=client.get("/api/v1/video-jobs/"+video_id,headers=auth_headers).json()
        if state["status"] in {"completed","failed"}:break
        time.sleep(.02)
    assert state["status"]=="completed"
    accepted=client.post("/api/v1/enrichment-jobs",headers=auth_headers,json={"source":{"kind":"video","source_id":video_id}})
    assert accepted.status_code==202
    job_id=accepted.json()["enrichment_job_id"]
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        job=client.get("/api/v1/enrichment-jobs/"+job_id,headers=auth_headers).json()
        if job["status"] in {"completed","failed"}:break
        time.sleep(.02)
    assert job["status"]=="completed"
    results=client.get("/api/v1/enrichment-jobs/"+job_id+"/results",headers=auth_headers).json()
    assert results["total"]>0
    assert all(item["track_id"] is not None for item in results["items"])
