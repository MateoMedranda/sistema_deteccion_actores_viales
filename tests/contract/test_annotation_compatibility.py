from tests.image_exploration_fixtures import scene_bytes
def test_existing_canonical_and_annotated_contract(enrichment_client, auth_headers):
    client=enrichment_client
    response=client.post("/api/v1/detections/images",headers=auth_headers,files={"image":("scene.jpg",scene_bytes(),"image/jpeg")})
    assert response.status_code==200, response.text
    data=response.json()
    for kind in ("original_image","annotated_image"):
        route=data[kind]["url"]
        assert client.get(route).status_code==401
        evidence=client.get(route,headers=auth_headers)
        assert evidence.status_code==200
        assert evidence.headers["cache-control"]=="no-store"
    for route in ("/api/v1/video-jobs","/api/v1/count-jobs","/api/v1/enrichment-jobs"):
        assert any(p.startswith(route) for p in client.get("/openapi.json").json()["paths"])
