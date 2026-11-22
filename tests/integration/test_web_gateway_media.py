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
