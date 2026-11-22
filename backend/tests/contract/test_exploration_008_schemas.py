"""Approved design examples and additive runtime responses stay compatible."""
import json
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker
from app.domain.schemas import VideoJobResponse
from app.api.routes.video_jobs import public_job
from app.services.video_job_store import VideoJobStore
from tests.unit.test_video_job_store import metadata
ROOT=Path(__file__).resolve().parents[3]
SCHEMA=json.loads((ROOT/"specs/008-exploracion-imagen-video/contracts/schemas.json").read_text(encoding="utf-8"))
EXAMPLES=json.loads((ROOT/"specs/008-exploracion-imagen-video/contracts/examples.json").read_text(encoding="utf-8"))
def validator(name):
 return Draft202012Validator({**SCHEMA,"$ref":"#/$defs/"+name},format_checker=FormatChecker())
def test_all_approved_examples():
 assert len(SCHEMA["$defs"])==16
 assert len(EXAMPLES["valid"])==13 and len(EXAMPLES["invalid"])==9
 for case in EXAMPLES["valid"]:validator(case["schema"]).validate(case["value"])
 for case in EXAMPLES["invalid"]:assert list(validator(case["schema"]).iter_errors(case["value"])),case
def test_new_and_historical_video_dtos(tmp_path):
 store=VideoJobStore(tmp_path/"jobs.sqlite",60,4)
 job=store.create("owner",metadata(),tmp_path/"input.mp4");store.dequeue()
 queued=public_job(store.get(job.job_id,"owner")).model_dump(mode="json")
 validator("VideoJobResponse").validate(queued)
 store.finish(job.job_id,tmp_path/"output.mp4",[],actual_frame_count=3,eligible_classes={"car"})
 ready=public_job(store.get(job.job_id,"owner")).model_dump(mode="json")
 validator("VideoJobResponse").validate(ready)
 assert ready["video_metadata"]["frame_count"]==3
 store.close()
def test_web_policy_openapi_is_additive():
 from app.main import app
 contract=app.openapi()
 assert "/api/v1/web-policy" in contract["paths"]
 assert "frame_total_confirmed" in contract["components"]["schemas"]["VideoJobResponse"]["properties"]
