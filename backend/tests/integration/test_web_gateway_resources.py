import httpx,pytest,subprocess,sys
from fastapi.testclient import TestClient
from tests.integration.test_web_gateway_security import fixture,bootstrap,POLICY
def test_large_upload_and_json_never_reach_upstream():
 app,calls,_=fixture()
 with TestClient(app,base_url="http://127.0.0.1:4173") as c:
  h=bootstrap(c);before=len(calls)
  assert c.post("/web-api/api/v1/detections/images",headers={**h,"Content-Type":"multipart/form-data; boundary=x"},content=b"x"*80000).status_code==413
  assert c.post("/web-api/api/v1/enrichment-jobs",headers=h,content=b"x"*17000).status_code==413
  assert len(calls)==before
  assert app.state.proxy.active==app.state.proxy.uploads==0
def test_large_upstream_json_is_rejected_and_releases_admission():
 def handler(req):
  if req.url.path.endswith("web-policy"):return httpx.Response(200,json=POLICY)
  return httpx.Response(200,json={"untrusted":"x"*(2*1024*1024)})
 app,_,_=fixture(handler)
 with TestClient(app,base_url="http://127.0.0.1:4173") as c:
  h=bootstrap(c);r=c.get("/web-api/health/live",headers=h)
  assert r.status_code==502 and len(r.content)<1024 and app.state.proxy.active==0
def test_admission_is_immediate_and_does_not_evict_session():
 app,_,_=fixture()
 with TestClient(app,base_url="http://127.0.0.1:4173") as c:
  h=bootstrap(c);app.state.proxy.active=16
  r=c.get("/web-api/health/live",headers=h)
  assert r.status_code==429 and r.headers["retry-after"]=="1"
  app.state.proxy.active=0
  assert c.get("/web-api/api/v1/web-policy",headers=h).status_code==200
def test_gateway_import_does_not_load_detector_app():
 result=subprocess.run([sys.executable,"-B","-c","import sys;import app.web.main;assert 'app.main' not in sys.modules;assert 'torch' not in sys.modules"],capture_output=True,timeout=20)
 assert result.returncode==0
