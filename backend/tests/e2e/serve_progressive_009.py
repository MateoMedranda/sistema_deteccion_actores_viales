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
enrichment_calls=0


class ControlledDetector:
    model_name = "controlled"

    def __init__(self):
        self.calls = 0

    def detect(self, image):
        self.calls += 1
        if mode == "fault" and self.calls > 180:
            raise RuntimeError("controlled_failure")
        time.sleep(0.005)
        if mode == "empty":
            return []
        h, w = image.shape[:2]
        y_offset=min(60,max(0,self.calls-15)) if mode=="count" else 0
        return [
            Detection(
                0,
                "car",
                0.9,
                20 + i % 5 * 100,
                30 + i // 5 * 150 + y_offset,
                100 + i % 5 * 100,
                130 + i // 5 * 150 + y_offset,
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
            processor=application.state.progressive_worker.processor
            enrich=processor.enrich
            def observed_enrich(*args,**kwargs):
                global enrichment_calls
                enrichment_calls+=1
                return enrich(*args,**kwargs)
            processor.enrich=observed_enrich
            store=application.state.progressive_store
            publish=store.publish
            def observed(job,frames,**kwargs):
                result=publish(job,frames,**kwargs)
                with store.lock:
                    row=store.row(job)
                    if row["until_us"]>=5_000_000:prefix_commits.setdefault(job,time.time()*1000)
                    reached=row["frames"]>=180
                # Hold analysis after commit, outside the model resource lock, so user-requested
                # enrichment can run while the test deliberately stops the next publication.
                if reached and mode in ("normal","count"):
                    while not release.wait(.05):pass
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
    return {"calls": detector.calls,"enrichment_calls":enrichment_calls}


@app.post("/test-only/reset")
def reset(scenario: str = "normal"):
    global mode,enrichment_calls
    release.set()
    store=app.state.progressive_store
    with store.lock:
        old=store.db.execute("SELECT job,owner FROM p_video WHERE retired=0").fetchall()
        for rec in old:store.withdraw(rec["job"],rec["owner"])
    mode = scenario
    enrichment_calls=0
    release.clear()
    detector.calls = 0
    prefix_commits.clear()
    if scenario in ("empty", "short", "fault"):
        release.set()
    return {"reset": True}

@app.get("/test-only/metrics")
def metrics(job:str):return {"five_seconds_commit_ms":prefix_commits.get(job)}
