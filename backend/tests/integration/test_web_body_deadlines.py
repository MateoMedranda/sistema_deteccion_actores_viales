import asyncio
import httpx
import pytest
from tests.integration.test_web_gateway_security import fixture
@pytest.mark.asyncio
async def test_slow_json_bodies_expire_and_release_admission(monkeypatch):
 app,_,_=fixture()
 timeout=asyncio.timeout
 monkeypatch.setattr("app.web.main.asyncio.timeout",lambda seconds:timeout(.02))
 async def slow():
  yield b"{"
  await asyncio.Event().wait()
 async with app.router.lifespan_context(app):
  async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url="http://127.0.0.1:4173") as client:
   base={"Origin":"http://127.0.0.1:4173","X-UI-Request":"1"}
   response=await client.post("/web/session",headers=base,content=slow())
   assert response.status_code==504
   ready=await client.post("/web/session",headers=base,json={})
   headers={**base,"X-UI-CSRF":ready.json()["csrf_token"]}
   response=await client.post("/web-api/api/v1/enrichment-jobs",headers=headers,content=slow())
   assert response.status_code==504 and app.state.proxy.active==0
