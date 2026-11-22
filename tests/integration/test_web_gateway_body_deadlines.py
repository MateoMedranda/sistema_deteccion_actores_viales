import asyncio
import httpx
import pytest
from tests.integration.test_web_gateway_security import fixture
@pytest.mark.asyncio
async def test_slow_bootstrap_and_json_body_timeout_without_holding_relay(monkeypatch):
 app,calls,_=fixture()
 original=asyncio.timeout
 monkeypatch.setattr(asyncio,"timeout",lambda seconds:original(min(seconds,.02)))
 async def stalled():
  yield b"{"
  await asyncio.Event().wait()
 async with app.router.lifespan_context(app):
  async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url="http://127.0.0.1:4173") as client:
   h={"Origin":"http://127.0.0.1:4173","X-UI-Request":"1","Content-Type":"application/json"}
   response=await client.post("/web/session",headers=h,content=stalled())
   assert response.status_code==504 and not calls
   response=await client.post("/web/session",headers=h,json={})
   assert response.status_code==200
   headers={**h,"X-UI-CSRF":response.json()["csrf_token"]}
   count=len(calls)
   response=await client.post("/web-api/api/v1/enrichment-jobs",headers=headers,content=stalled())
   assert response.status_code==504 and len(calls)==count
   assert app.state.proxy.active==0 and app.state.proxy.uploads==0
