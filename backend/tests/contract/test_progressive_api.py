from tests.fixtures_progressive import video
def test_opt_in_keeps_legacy_receipt_and_separates_idempotency(client,tmp_path,auth_headers):
 path=video(tmp_path/"source.mp4");body=lambda:{"video":("source.mp4",path.read_bytes(),"video/mp4")}
 key={**auth_headers,"Idempotency-Key":"progressive-contract-intent"}
 first=client.post("/api/v1/video-jobs?presentation=progressive",headers=key,files=body())
 assert first.status_code==202,first.text
 assert set(first.json())=={"job_id","status","created_at"}
 repeat=client.post("/api/v1/video-jobs?presentation=progressive",headers=key,files=body())
 assert repeat.status_code==202 and repeat.json()==first.json()
 assert client.post("/api/v1/video-jobs",headers=key,files=body()).status_code==409
 for query in ("presentation=unknown","presentation=progressive&presentation=progressive","extra=1"):
  assert client.post("/api/v1/video-jobs?"+query,headers=auth_headers,files=body()).status_code==422
 legacy=client.post("/api/v1/video-jobs",headers=auth_headers,files=body())
 assert legacy.status_code==202
 assert client.get("/api/v1/video-jobs/"+legacy.json()["job_id"]+"/playback",headers=auth_headers).status_code==404
