import httpx
from fastapi.testclient import TestClient
from tests.integration.test_web_gateway_security import fixture,bootstrap,POLICY
A="00000000-0000-4000-8000-000000000001";B="00000000-0000-4000-8000-000000000002"
def test_video_intent_required_same_retry_is_bound_and_late_generation_rejected():
 keys=[]
 def handler(req):
  if req.url.path.endswith("web-policy"):return httpx.Response(200,json=POLICY)
  keys.append(req.headers.get("idempotency-key"))
  return httpx.Response(202,json={"job_id":"video","status":"queued","created_at":"2040-01-01T00:00:00Z"})
 app,calls,key=fixture(handler)
 with TestClient(app,base_url="http://127.0.0.1:4173") as c:
  h=bootstrap(c);url="/web-api/api/v1/video-jobs"
  assert c.post(url,headers=h,files={"video":("a.mp4",b"fake","video/mp4")}).status_code==422
  for _ in range(2):
   assert c.post(url,headers={**h,"X-UI-Intent":A,"X-UI-Intent-Generation":"1"},files={"video":("a.mp4",b"fake","video/mp4")}).status_code==202
  assert keys[0]==keys[1] and keys[0]!=key
  c.post(url,headers={**h,"X-UI-Intent":B,"X-UI-Intent-Generation":"2"},files={"video":("b.mp4",b"fake","video/mp4")})
  n=len(calls)
  assert c.post(url,headers={**h,"X-UI-Intent":A,"X-UI-Intent-Generation":"1"},files={"video":("a.mp4",b"fake","video/mp4")}).status_code==409
  assert len(calls)==n
def test_image_without_intent_remains_compatible():
 app,_,_=fixture(lambda req:httpx.Response(200,json=POLICY) if req.url.path.endswith("web-policy") else httpx.Response(202,json={"status":"queued"}))
 with TestClient(app,base_url="http://127.0.0.1:4173") as c:
  h=bootstrap(c)
  assert c.post("/web-api/api/v1/enrichment-jobs",headers=h,json={"source":{"kind":"image","source_id":"image"}}).status_code==202
