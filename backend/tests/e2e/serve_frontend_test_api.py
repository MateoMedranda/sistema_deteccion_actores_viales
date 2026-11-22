"""Isolated deterministic API for browser tests; not a production entry point."""
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import time
from app.main import create_app
from app.core.config import Settings
from app.adapters.plate_localizer_protocol import PlateLocation
from tests.image_exploration_fixtures import SceneDetector
from tests.e2e.annotation_adapters import AnnotationDetector,AnnotationLocalizer,AnnotationReader,AnnotationAttributes,COUNTS
from tests.enrichment_fixtures import FakeAttributes, FakeReader

class DemoLocalizer:
    def locate(self, crop):
        h, w = crop.shape[:2]
        return PlateLocation(int(w*.12), int(h*.65), int(w*.52), int(h*.82), .95)

class DemoReader(FakeReader):
    def read(self, crop):
        time.sleep(.25)
        return super().read(crop)

_runtime = TemporaryDirectory(prefix="road-ui-test-")
_path = Path(_runtime.name)
settings = Settings(
    _env_file=None, api_key="ui-synthetic-key",
    frontend_allowed_origins="http://127.0.0.1:4173",
    temp_artifact_dir=_path/"annotated",
    video_job_db_path=_path/"video.sqlite3", video_temp_dir=_path/"video",
    count_job_db_path=_path/"count.sqlite3", count_temp_dir=_path/"count",
    enrichment_job_db_path=_path/"enrichment.sqlite3", enrichment_temp_dir=_path/"sources",
    attribute_model_weights_path=_path/"synthetic.pt",
    attribute_model_manifest_path=_path/"synthetic.json",
    plate_model_weights_path=_path/"plate.pt",
)
app = create_app(settings, AnnotationDetector())
_original_lifespan = app.router.lifespan_context

@asynccontextmanager
async def test_lifespan(application):
    with patch("app.core.lifespan.EfficientNetAttributeExtractor", lambda *a: AnnotationAttributes()), \
         patch("app.core.lifespan.YOLOv8PlateLocalizer", lambda *a: AnnotationLocalizer()), \
         patch("app.core.lifespan.PaddlePlateReader", lambda *a: AnnotationReader()):
        async with _original_lifespan(application):
            import logging
            logging.getLogger("road_actor_detection").setLevel(logging.WARNING)
            yield
app.router.lifespan_context = test_lifespan

# Only this isolated test application exposes cache controls/counters.
from fastapi import Depends
from app.api.dependencies import require_api_key
@app.get("/test-only/preview-control",dependencies=[Depends(require_api_key)])
def preview_control():
    return {"models":dict(COUNTS),"entries":app.state.plate_preview_store.entry_count,"bytes":app.state.plate_preview_store.byte_count}
@app.delete("/test-only/preview-control",dependencies=[Depends(require_api_key)])
def clear_preview_cache():
    store=app.state.plate_preview_store
    with store.lock:
        store.cache.clear();store.bytes=0
    return {"cleared":True}
