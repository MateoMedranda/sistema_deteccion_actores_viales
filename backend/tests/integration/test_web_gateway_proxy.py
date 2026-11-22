import httpx
from fastapi.testclient import TestClient
from tests.integration.test_web_gateway_security import fixture,bootstrap
def test_allowlist_and_query_are_closed_before_upstream():
 app,calls,key=fixture()
 with TestClient(app,base_url="http://127.0.0.1:4173") as c:
  h=bootstrap(c);n=len(calls)
  for path in ["/admin","/api/v1/video-jobs/a/detections?page=0","/api/v1/video-jobs/a/detections?page=1&page=2","/api/v1/video-jobs/a?target=http://evil.invalid","/api/v1/video-jobs/a%252fb"]:
   assert c.get("/web-api"+path,headers=h).status_code in (404,422)
  assert len(calls)==n
def test_caller_credentials_are_discarded_and_redirect_is_not_followed():
 def handler(req):
  if req.url.path.endswith("web-policy"):return httpx.Response(200,json=__import__("tests.integration.test_web_gateway_security",fromlist=["POLICY"]).POLICY)
  assert req.headers["x-api-key"]!="attacker";assert "cookie" not in req.headers and "authorization" not in req.headers
  return httpx.Response(302,headers={"Location":"http://private.invalid"})
 app,calls,key=fixture(handler)
 with TestClient(app,base_url="http://127.0.0.1:4173") as c:
  h=bootstrap(c);r=c.get("/web-api/health/live",headers={**h,"X-API-Key":"attacker","Authorization":"Bearer attacker"})
  assert r.status_code==502 and "private.invalid" not in r.text
