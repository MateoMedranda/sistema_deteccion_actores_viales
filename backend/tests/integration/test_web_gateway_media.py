import httpx
from fastapi.testclient import TestClient
from tests.integration.test_web_gateway_security import fixture,bootstrap,POLICY
def test_native_media_is_cookie_only_exact_path_and_preserves_range():
 def handler(req):
  if req.url.path.endswith("web-policy"):return httpx.Response(200,json=POLICY)
  if req.url.path.endswith("/content"):
   assert req.headers["range"]=="bytes=0-3"
   return httpx.Response(206,content=b"mp4!",headers={"Content-Type":"video/mp4","Content-Range":"bytes 0-3/8","Accept-Ranges":"bytes"})
  return httpx.Response(200,json={"status":"completed","expires_at":"2040-01-01T00:00:00Z"})
 app,_,_=fixture(handler)
 with TestClient(app,base_url="http://127.0.0.1:4173") as c:
  bootstrap(c)
  r=c.get("/web-api/api/v1/video-jobs/a/annotated-video/content",headers={"Range":"bytes=0-3"})
  assert r.status_code==206 and r.content==b"mp4!" and r.headers["cross-origin-resource-policy"]=="same-origin"
  assert c.get("/web-api/api/v1/video-jobs/a/annotated-video/content",headers={"Range":"bytes=0-3,5-7"}).status_code==416


def test_explicit_export_is_forwarded_only_with_session_and_csrf():
 def handler(req):
  if req.url.path.endswith("web-policy"):return httpx.Response(200,json=POLICY)
  return httpx.Response(202,json={"job_id":"a","state":"queued"})
 app,calls,_=fixture(handler)
 with TestClient(app,base_url="http://127.0.0.1:4173") as c:
  headers=bootstrap(c)
  url="/web-api/api/v1/video-jobs/a/playback/export"
  assert c.post(url,headers={"Origin":"http://127.0.0.1:4173","X-UI-Request":"1"}).status_code==403
  assert c.post(url,headers=headers).status_code==202
  assert sum(req.method=="POST" and req.url.path.endswith("/playback/export") for req in calls)==1
  assert c.post(url+"?url=http://evil.invalid",headers=headers).status_code==422
