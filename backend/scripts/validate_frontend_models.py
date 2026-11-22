"""Run approved adapters against local media with isolated stores and a redacted report."""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import UTC, datetime
import json
import logging
from pathlib import Path
from tempfile import TemporaryDirectory
import time
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.core.config import Settings
from app.main import create_app

class Measurements(logging.Handler):
    def __init__(self):
        super().__init__(); self.records=[]
    def emit(self, record):
        if record.msg == "inference_measurement":
            self.records.append({k:getattr(record,k,None) for k in (
                "branch","duration_ms","initial_memory_mb","memory_mb","peak_memory_mb","status","error_code")})

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--media-manifest",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    paths=json.loads(args.media_manifest.read_text(encoding="utf-8"))["images"]
    report={"timestamp":datetime.now(UTC).isoformat(),"kind":"real-model smoke; no labelled reference or baseline comparison","images":[]}
    measurements=Measurements(); logger=logging.getLogger("006.real.validation");logger.handlers=[measurements];logger.propagate=False;logger.setLevel(logging.INFO)
    with TemporaryDirectory(prefix="006-approved-models-") as runtime:
        root=Path(runtime)
        settings=Settings().model_copy(update={"api_key":"isolated-real-test-key","api_keys":None,
            "temp_artifact_dir":root/"annotated","video_job_db_path":root/"video.sqlite3",
            "video_temp_dir":root/"video","count_job_db_path":root/"count.sqlite3","count_temp_dir":root/"count",
            "enrichment_job_db_path":root/"enrichment.sqlite3","enrichment_temp_dir":root/"sources"})
        with patch("app.core.lifespan.configure_logging",return_value=logger), TestClient(create_app(settings)) as client:
            report["readiness"]={"detection":client.get("/health/ready").status_code,
                "enrichment":client.get("/health/enrichment-ready").json()}
            headers={"X-API-Key":"isolated-real-test-key"}
            for ordinal,path in enumerate(paths[:10],1):
                data=Path(path).read_bytes(); suffix=Path(path).suffix.lower(); mime="image/png" if suffix==".png" else "image/jpeg"
                started=time.perf_counter()
                response=client.post("/api/v1/detections/images",headers=headers,files={"image":("controlled"+suffix,data,mime)})
                item={"ordinal":ordinal,"http_status":response.status_code,"request_ms":round((time.perf_counter()-started)*1000,2)}
                if response.status_code==200:
                    source=response.json(); item["detections"]=len(source["detections"]);item["eligible"]=sum(d["enrichment_eligible"] for d in source["detections"])
                    item["original_status"]=client.get(source["original_image"]["url"],headers=headers).status_code
                    if item["eligible"]:
                        accepted=client.post("/api/v1/enrichment-jobs",headers=headers,json={"source":{"kind":"image","source_id":source["request_id"]}})
                        item["creation_status"]=accepted.status_code
                        if accepted.status_code==202:
                            job_id=accepted.json()["enrichment_job_id"];deadline=time.monotonic()+120
                            while time.monotonic()<deadline:
                                job=client.get("/api/v1/enrichment-jobs/"+job_id,headers=headers).json()
                                if job["status"] in {"completed","failed","cancelled"}:break
                                time.sleep(.1)
                            item["enrichment_status"]=job["status"]
                            if job["status"]=="completed":
                                results=client.get("/api/v1/enrichment-jobs/"+job_id+"/results?page_size=100",headers=headers).json()
                                item["results"]=results["total"];item["plate_states"]=dict(Counter(r["plate_status"] for r in results["items"]))
                                item["attributes_states"]=dict(Counter(r["attributes_status"] for r in results["items"]))
                report["images"].append(item)
                print("REAL_MODEL_SAMPLE",json.dumps(item),flush=True)
    report["measurements"]=measurements.records
    import importlib.metadata,platform
    report["environment"]={"python":platform.python_version(),"platform":platform.platform(),"versions":{p:importlib.metadata.version(p) for p in ("torch","torchvision","paddleocr","paddlepaddle","ultralytics")}}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print("REAL_MODEL_REPORT_WRITTEN",flush=True)
if __name__=="__main__":main()
