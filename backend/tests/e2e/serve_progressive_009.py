"""Synthetic, isolated browser fixture. Never imports private .env."""

from pathlib import Path
from tempfile import TemporaryDirectory
from contextlib import asynccontextmanager
from unittest.mock import patch
import threading, time, logging
from app.core.config import Settings
from app.main import create_app
from app.domain.models import Detection
from tests.enrichment_fixtures import FakeAttributes, FakeLocalizer, FakeReader

runtime = TemporaryDirectory(prefix="progressive-009-")
root = Path(runtime.name)
release = threading.Event()
mode = "normal"
prefix_commits={}


class ControlledDetector:
    model_name = "controlled"

    def __init__(self):
        self.calls = 0

    def detect(self, image):
        self.calls += 1
        if mode == "fault" and self.calls > 180:
            raise RuntimeError("controlled_failure")
        if self.calls > 180:
            while not release.wait(0.05):
                pass
        time.sleep(0.005)
        if mode == "empty":
            return []
        h, w = image.shape[:2]
        return [
            Detection(
                0,
                "car",
                0.9,
                20 + i % 5 * 100,
                30 + i // 5 * 150,
                100 + i % 5 * 100,
                130 + i // 5 * 150,
            )
            for i in range(10)
        ]


detector = ControlledDetector()
settings = Settings(
    _env_file=None,
    api_key="controlled-009",
    temp_artifact_dir=root / "images",
    video_job_db_path=root / "video.sqlite3",
    video_temp_dir=root / "video",
    count_job_db_path=root / "count.sqlite3",
    count_temp_dir=root / "count",
    enrichment_job_db_path=root / "enrich.sqlite3",
    enrichment_temp_dir=root / "enrich",
    attribute_model_weights_path=root / "attrs",
    attribute_model_manifest_path=root / "manifest",
    plate_model_weights_path=root / "plate",
    frontend_allowed_origins="http://127.0.0.1:9413",
)
app = create_app(settings, detector)
original = app.router.lifespan_context


@asynccontextmanager
async def lifespan(application):
    with (
        patch("app.core.lifespan.EfficientNetAttributeExtractor", lambda *a: FakeAttributes()),
        patch("app.core.lifespan.YOLOv8PlateLocalizer", lambda *a: FakeLocalizer()),
        patch("app.core.lifespan.PaddlePlateReader", lambda *a: FakeReader()),
    ):
        async with original(application):
            store=application.state.progressive_store
            publish=store.publish
            def observed(job,frames,**kwargs):
                result=publish(job,frames,**kwargs)
                with store.lock:
                    row=store.row(job)
                    if row["until_us"]>=5_000_000:prefix_commits.setdefault(job,time.time()*1000)
                return result
            store.publish=observed
            logging.getLogger("road_actor_detection").setLevel(logging.ERROR)
            try:
                yield
            finally:
                release.set()


app.router.lifespan_context = lifespan


@app.post("/test-only/release")
def unlock():
    release.set()
    return {"released": True}


@app.get("/test-only/calls")
def calls():
    return {"calls": detector.calls}


@app.post("/test-only/reset")
def reset(scenario: str = "normal"):
    global mode
    mode = scenario
    release.clear()
    detector.calls = 0
    prefix_commits.clear()
    if scenario in ("empty", "short", "fault"):
        release.set()
    return {"reset": True}

@app.get("/test-only/metrics")
def metrics(job:str):return {"five_seconds_commit_ms":prefix_commits.get(job)}
