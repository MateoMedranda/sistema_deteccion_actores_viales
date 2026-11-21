import time,json
from tests.image_exploration_fixtures import scene_bytes
def completed(client,headers):
    import cv2,numpy as np
    image=np.indices((400,640)).sum(axis=0).astype(np.uint8)
    ok,encoded=cv2.imencode(".png",image)
    source=client.post("/api/v1/detections/images",headers=headers,files={"image":("scene.png",encoded.tobytes(),"image/png")}).json()
    job=client.post("/api/v1/enrichment-jobs",headers=headers,json={"source":{"kind":"image","source_id":source["request_id"]}}).json()["enrichment_job_id"]
    for _ in range(100):
        if client.get("/api/v1/enrichment-jobs/"+job,headers=headers).json()["status"]=="completed":break
        time.sleep(.03)
    return source,job
def test_preview_is_protected_no_inference_and_has_provenance(enrichment_client,auth_headers):
    c=enrichment_client;source,job=completed(c,auth_headers)
    url=f"/api/v1/enrichment-jobs/{job}/detections/1/plate-preview"
    response=c.get(url,headers={**auth_headers,"Origin":"http://localhost:5173"})
    assert response.status_code==200,response.text
    assert response.headers["content-type"]=="image/png"
    metadata=json.loads(response.headers["x-plate-preview-metadata"])
    assert metadata["source_id"]==source["request_id"] and metadata["enrichment_job_id"]==job
    assert metadata["detection_id"]==1 and metadata["profile_id"]=="display-contrast-v1"
    assert response.content.startswith(b"\x89PNG")
    assert c.get(url,headers=auth_headers).content==response.content
    assert c.get(url+"?profile=unknown",headers=auth_headers).status_code==422
    assert c.get(url.replace("/1/","/999/"),headers=auth_headers).status_code==404
