import httpx,pytest
from fastapi.testclient import TestClient
from app.web.main import create_web_app
from app.web.settings import WebSettings
POLICY={"image":{"media_types":["image/jpeg","image/png"],"max_upload_bytes":10000,"max_image_pixels":10000},"video":{"media_types":["video/mp4"],"max_upload_bytes":100000,"max_duration_seconds":120,"max_width":1920,"max_height":1080,"max_fps":30,"max_frames":3600},"capabilities":{"image_detection":True,"video_analysis":True,"attributes":True,"plates":True}}
def fixture(handler=None,**kwargs):
 key="canary-"+__import__("secrets").token_hex(24)
 settings=WebSettings(_env_file=None,backend_url="http://127.0.0.1:8000",backend_api_key=key,origin="http://127.0.0.1:4173",**kwargs)
 calls=[]
 def upstream(req):
  calls.append(req);assert req.headers["x-api-key"]==key
  return handler(req) if handler else httpx.Response(200,json=POLICY)
 return create_web_app(settings,transport=httpx.MockTransport(upstream)),calls,key
def bootstrap(client):
 r=client.post("/web/session",headers={"Origin":"http://127.0.0.1:4173","X-UI-Request":"1"},json={})
 assert r.status_code==200,r.text
 return {"X-UI-Request":"1","X-UI-CSRF":r.json()["csrf_token"],"Origin":"http://127.0.0.1:4173"}
def test_bootstrap_never_returns_secret_and_guards_csrf_host_origin():
 app,calls,key=fixture()
 with TestClient(app,base_url="http://127.0.0.1:4173") as c:
  assert c.post("/web/session",json={}).status_code==403
  headers=bootstrap(c);assert key not in c.get("/health/live").text
  assert c.get("/web-api/api/v1/web-policy").status_code==403
  assert c.get("/web-api/api/v1/web-policy",headers=headers).status_code==200
  assert c.post("/web-api/api/v1/video-jobs",headers={**headers,"Origin":"http://evil.invalid"},content=b"x").status_code==403
  assert c.delete("/web/session",headers=headers).status_code==204
  assert c.get("/web-api/api/v1/web-policy",headers=headers).status_code==401
def test_invalid_and_missing_configuration_are_safe():
 for settings in [WebSettings(_env_file=None),WebSettings(_env_file=None,backend_url="http://remote.invalid",backend_api_key="secret")]:
  with TestClient(create_web_app(settings)) as c:
   r=c.post("/web/session",headers={"Origin":"http://127.0.0.1:4173","Host":"127.0.0.1:4173","X-UI-Request":"1"},json={})
   assert r.status_code==503 and "secret" not in r.text and "remote.invalid" not in r.text
