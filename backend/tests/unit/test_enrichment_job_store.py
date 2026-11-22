from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.services.enrichment_job_store import EnrichmentJobStore


def test_store_persists_redacted_plate_only_when_read(tmp_path) -> None:
    store = EnrichmentJobStore(tmp_path / "enrichment.sqlite3", 60, 2)
    job = store.create("image", "source", "owner", 1, datetime.now(UTC) + timedelta(seconds=60))
    assert store.dequeue() is not None
    store.finish(job.enrichment_job_id, [{"vehicle_key": "detection-1", "detection_id": 1, "track_id": None, "class_id": 0, "class_name": "car", "evidence_frame_indexes": [], "attributes_status": "completed", "plate_status": "unreadable", "attributes": [{"name": "color", "label": "white", "confidence": .9, "evidence_frame_index": None}], "plate": {"status": "unreadable", "used_enhancement": False, "evidence_frame_indexes": [], "text": "must-not-store"}, "error_code": None}])
    stored = store.connection.execute("SELECT plate_text FROM enrichment_plates").fetchone()[0]
    assert stored is None
    assert store.get(job.enrichment_job_id, "owner").status.value == "completed"
    store.close()
