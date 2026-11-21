"""Shared deterministic 007 fixtures. No private runtime or model loading."""
from threading import Event
from tests.image_exploration_fixtures import scene_bytes, SceneDetector
from tests.enrichment_fixtures import FakeAttributes, FakeReader
class Clock:
    def __init__(self, value=0): self.value=value
    def __call__(self): return self.value
    def advance(self, seconds): self.value+=seconds
class Barrier:
    def __init__(self): self.started=Event(); self.release=Event()
    def __call__(self): self.started.set(); self.release.wait(15)
class CountedReader(FakeReader):
    def __init__(self): self.calls=0
    def read(self,crop): self.calls+=1; return super().read(crop)
