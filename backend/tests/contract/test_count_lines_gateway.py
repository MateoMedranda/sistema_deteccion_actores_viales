import httpx,pytest
from fastapi.testclient import TestClient
from starlette.datastructures import QueryParams
from app.web.proxy import classify,RelayError
from tests.integration.test_web_gateway_security import fixture,bootstrap,POLICY
BASE='/api/v1/video-jobs/test/playback/count-lines'
@pytest.mark.parametrize('method,suffix,query',[('GET','','generation=11111111-1111-4111-8111-111111111111'),('PUT','',''),('GET','/counts','generation=11111111-1111-4111-8111-111111111111&revision=0&at_us=0'),('POST','/import-legacy','')])
def test_exact_allowlist(method,suffix,query):assert classify(method,BASE+suffix,(BASE+suffix).encode(),QueryParams(query))=='json'
@pytest.mark.parametrize('method,suffix,query',[('POST','',''),('DELETE','',''),('PUT','','generation=11111111-1111-4111-8111-111111111111'),('GET','/counts','at_us=0&at_us=1'),('POST','/import-legacy','generation=11111111-1111-4111-8111-111111111111'),('GET','','url=http://elsewhere')])
def test_query_and_methods_closed(method,suffix,query):
 with pytest.raises(RelayError):classify(method,BASE+suffix,(BASE+suffix).encode(),QueryParams(query))
def test_gateway_csrf_limits_and_no_secret_leak():
 def handler(req):return httpx.Response(200,json=POLICY if req.url.path.endswith('web-policy') else {'safe':True})
 app,calls,key=fixture(handler)
 with TestClient(app,base_url='http://127.0.0.1:4173') as c:
  h=bootstrap(c);url='/web-api'+BASE
  assert c.put(url,headers={**h,'Origin':'http://evil.invalid'},json={}).status_code==403
  assert c.put(url,headers=h,content=b' '*65537).status_code==413
  response=c.put(url,headers=h,json={});assert response.status_code==200 and response.headers['cache-control']=='no-store' and key not in response.text
  assert c.get(url+'?generation=11111111-1111-4111-8111-111111111111&generation=y',headers=h).status_code==422
