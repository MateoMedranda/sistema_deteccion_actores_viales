import json
from datetime import UTC, datetime, timedelta
import pytest
from app.services.enrichment_results import normalize_results
from app.services.enrichment_job_store import EnrichmentJobStore

def result(status="read"):
    return {"vehicle_key":"detection-1","detection_id":1,"track_id":None,"class_id":0,"class_name":"car",
        "evidence_frame_indexes":[],"attributes_status":"completed","attributes":[],
        "plate_status":status,"plate":{"status":status,"text":"SYN_CANARY",
        "bbox_relative":{"x_min":.1,"y_min":.2,"x_max":.4,"y_max":.3},
        "used_enhancement":False,"evidence_frame_indexes":[]},"error_code":None}

@pytest.mark.parametrize("status",["unreadable","not_detected","failed"])
def test_text_is_removed_from_every_non_read_representation(tmp_path,status):
    store=EnrichmentJobStore(tmp_path/"jobs.sqlite3",60,3)
    job=store.create("image","source","owner",1,datetime.now(UTC)+timedelta(seconds=60))
    store.dequeue()
    store.finish(job.enrichment_job_id,[result(status)])
    raw=store.connection.execute("SELECT results_json FROM enrichment_jobs").fetchone()[0]
    assert "SYN_CANARY" not in raw
    assert store.connection.execute("SELECT plate_text FROM enrichment_plates").fetchone()[0] is None
    items,total=store.results(job.enrichment_job_id,"owner",1,50)
    assert total==1 and items[0]["plate"]["text"] is None
    if status=="failed":
        assert items[0]["plate"]["bbox_relative"]["x_min"]==.1
    store.close()

def test_invalid_confidence_is_rejected_before_persistence():
    item=result()
    item["attributes"]=[{"name":"color","label":"white","confidence":2}]
    with pytest.raises(ValueError):
        normalize_results([item])

def test_duplicate_identity_and_inconsistent_plate_status_are_rejected():
    with pytest.raises(ValueError):
        normalize_results([result(),result()])
    item=result()
    item["plate_status"]="failed"
    with pytest.raises(ValueError):
        normalize_results([item])
