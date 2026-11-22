"""Reusable deterministic controls, deliberately independent of the model lifespan."""
import asyncio
from datetime import UTC,datetime,timedelta
import httpx
class Clock:
    def __init__(self):self.value=datetime(2040,1,1,tzinfo=UTC)
    def __call__(self):return self.value
    def advance(self,seconds):self.value+=timedelta(seconds=seconds)
class Barrier:
    def __init__(self):self.entered=asyncio.Event();self.release=asyncio.Event()
    async def wait(self):self.entered.set();await self.release.wait()
OWNERS=("owner-alpha","owner-beta")
def upstream(handler):return httpx.MockTransport(handler)
