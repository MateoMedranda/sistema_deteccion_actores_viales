def test_policy_requires_owner_and_exposes_only_limits(client,auth_headers):
 assert client.get("/api/v1/web-policy").status_code==401
 r=client.get("/api/v1/web-policy",headers=auth_headers)
 assert r.status_code==200
 assert set(r.json())=={"image","video","capabilities"}
 assert r.json()["video"]["max_upload_bytes"]==100*1024*1024
 assert r.headers["cache-control"]=="no-store"
