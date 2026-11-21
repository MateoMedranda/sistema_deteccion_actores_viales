import asyncio
from io import BytesIO
from threading import Event
from types import SimpleNamespace
from unittest.mock import patch
import httpx
from fastapi import FastAPI
from PIL import Image
from starlette.datastructures import UploadFile,Headers
from app.core.config import Settings
from app.services.image_validation import ImageValidator

def test_normalization_does_not_block_other_api_requests():
    entered,released=Event(),Event()
    image=BytesIO();Image.new("RGB",(10,10)).save(image,format="PNG")
    validator=ImageValidator(Settings(_env_file=None,api_key="test"))
    original=Image.Image.save
    def save(self,*args,**kwargs):
        if kwargs.get("format")=="PNG":
            entered.set()
            assert released.wait(2)
        return original(self,*args,**kwargs)
    app=FastAPI()
    @app.post("/image")
    async def image_route():
        upload=UploadFile(BytesIO(image.getvalue()),filename="scene.png",headers=Headers({"content-type":"image/png"}))
        return {"width":(await validator.validate(upload)).width}
    @app.get("/health")
    async def health():
        return {"alive":True}
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url="http://test") as client:
            task=asyncio.create_task(client.post("/image"))
            try:
                assert await asyncio.to_thread(entered.wait,1)
                response=await asyncio.wait_for(client.get("/health"),.5)
                assert response.status_code==200
                assert not task.done()
            finally:
                released.set()
                await task
    with patch.object(Image.Image,"save",save):
        asyncio.run(run())
