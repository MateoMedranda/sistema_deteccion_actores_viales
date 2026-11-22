import logging
from types import SimpleNamespace
import cv2,numpy as np
import pytest
from app.api.error_handlers import ApiError
from app.services.enrichment_worker import EnrichmentWorker
from app.domain.models import Detection

@pytest.mark.parametrize("status",["cancelled","expired"])
def test_unit_metrics_do_not_claim_completion_before_any_inference(caplog,status):
    class Jobs:
        count=0
        def is_processing(self,*args):self.count+=1;return self.count<3
        def get(self,*args):
            if status=="expired":raise ApiError(410,"job_expired","safe")
            return SimpleNamespace(status=SimpleNamespace(value=status))
    class Processor:
        def enrich(self,*args,**kwargs):raise AssertionError("must not infer")
    d=Detection(0,"car",.9,0,0,10,10)
    _,png=cv2.imencode(".png",np.zeros((10,10,3),dtype=np.uint8))
    service=SimpleNamespace(resolve=lambda *a:SimpleNamespace(),units_for_source=lambda *a:[{"bbox":d}],images=SimpleNamespace(read_original=lambda *a:(png.tobytes(),None)))
    job=SimpleNamespace(source_id="source",enrichment_job_id="job",source_kind="image",owner_key_id="owner")
    with caplog.at_level(logging.INFO):
        EnrichmentWorker(Jobs(),service,Processor(),logging.getLogger("unit.metrics"))._process(job)
    events=[r for r in caplog.records if r.msg=="inference_measurement"]
    assert {r.branch for r in events}=={"enrichment_unit","enrichment_job"}
    assert all(r.status==status for r in events)
    assert all(r.request_id=="source" and r.job_id=="job" and r.duration_ms>=0 and r.memory_mb>0 for r in events)

@pytest.mark.parametrize("status",["cancelled","expired"])
def test_unit_metrics_stop_between_evidence_frames(caplog,status):
    class Jobs:
        state="processing"
        def is_processing(self,*a):return self.state=="processing"
        def get(self,*a):
            if self.state=="expired":raise ApiError(410,"job_expired","safe")
            return SimpleNamespace(status=SimpleNamespace(value=self.state))
    jobs=Jobs()
    class Processor:
        calls=0
        def enrich(self,*a,**kw):
            self.calls+=1;jobs.state=status
            return ({"status":"completed","items":[]},{"status":"not_detected","used_enhancement":False,"evidence_frame_indexes":[]})
    d=Detection(0,"car",.9,0,0,10,10);_,png=cv2.imencode(".png",np.zeros((10,10,3),dtype=np.uint8));processor=Processor()
    service=SimpleNamespace(resolve=lambda *a:SimpleNamespace(),units_for_source=lambda *a:[{"bbox":d,"evidence":[d,d]}],images=SimpleNamespace(read_original=lambda *a:(png.tobytes(),None)),settings=SimpleNamespace(vehicle_class_set=lambda:{"car"}))
    job=SimpleNamespace(source_id="source",enrichment_job_id="job",source_kind="image",owner_key_id="owner")
    with caplog.at_level(logging.INFO):EnrichmentWorker(jobs,service,processor,logging.getLogger("unit.metrics"))._process(job)
    assert processor.calls==1
    events=[r for r in caplog.records if r.msg=="inference_measurement"]
    assert all(r.status==status for r in events)

@pytest.mark.parametrize(
    ("scenario", "expected_status"),
    [
        ("completed", "completed"),
        ("cancelled", "cancelled"),
        ("expired_before", "expired"),
        ("expired_during", "expired"),
        ("expired_after_commit", "completed"),
        ("expired_after_cancel", "cancelled"),
    ],
)
def test_job_metric_matches_atomic_finalization(
    tmp_path, caplog, monkeypatch, scenario, expected_status
):
    from datetime import UTC, datetime, timedelta
    from app.core.logging import JsonFormatter
    from app.services.enrichment_job_store import EnrichmentJobStore
    from app.services.enrichment_processing import EnrichmentProcessor
    from tests.enrichment_fixtures import (
        FakeAttributes, FakeLocalizer, FakeReader,
        SYNTHETIC_IMAGE, VEHICLE_DETECTION,
    )

    clock = [datetime.now(UTC)]
    jobs = EnrichmentJobStore(
        tmp_path / "jobs.sqlite3", 60, 3, clock=lambda: clock[0]
    )
    created = jobs.create(
        "image", "source", "owner", 1, clock[0] + timedelta(seconds=60)
    )
    job = jobs.dequeue()
    logger = logging.getLogger("test.atomic-finalization")
    processor = EnrichmentProcessor(
        FakeAttributes(), FakeLocalizer(), FakeReader(), .7, .8
    )
    processor.logger = logger
    ok, png = cv2.imencode(".png", SYNTHETIC_IMAGE)
    assert ok
    service = SimpleNamespace(
        resolve=lambda *args: SimpleNamespace(),
        units_for_source=lambda *args: [{
            "bbox": VEHICLE_DETECTION, "track_id": None, "detection_id": 1,
            "class_id": 0, "class_name": "car",
        }],
        images=SimpleNamespace(read_original=lambda *args: (png.tobytes(), None)),
        settings=SimpleNamespace(vehicle_class_set=lambda: {"car"}),
    )

    original_finish = jobs.finish
    original_persist = jobs._persist_results

    def persist_then_expire(job_id, results):
        original_persist(job_id, results)
        assert jobs.connection.execute(
            "SELECT count(*) FROM enrichment_plates"
        ).fetchone()[0] == 1
        clock[0] += timedelta(seconds=61)

    if scenario == "expired_during":
        monkeypatch.setattr(jobs, "_persist_results", persist_then_expire)

    def finish_after_interleaving(job_id, results):
        # This boundary is after the worker's last cooperative state check.
        if scenario in {"cancelled", "expired_after_cancel"}:
            jobs.cancel(job_id, "owner")
        elif scenario == "expired_before":
            clock[0] += timedelta(seconds=61)
        outcome = original_finish(job_id, results)
        if scenario in {"expired_after_commit", "expired_after_cancel"}:
            # A later cleanup must not rewrite the outcome of finalization.
            clock[0] += timedelta(seconds=61)
            jobs.cleanup()
        return outcome

    monkeypatch.setattr(jobs, "finish", finish_after_interleaving)
    try:
        with caplog.at_level(logging.INFO, logger=logger.name):
            EnrichmentWorker(jobs, service, processor, logger)._process(job)
        events = [
            record for record in caplog.records
            if record.name == logger.name and record.msg == "inference_measurement"
        ]
        assert {record.branch for record in events} == {
            "attributes", "plate_localization", "plate_ocr", "plate",
            "enrichment_unit", "enrichment_job",
        }
        assert all(
            record.status == "completed"
            for record in events if record.branch != "enrichment_job"
        )
        for record in events:
            assert record.request_id == "source"
            assert record.job_id == created.enrichment_job_id
            assert record.duration_ms >= 0
            assert record.initial_memory_mb > 0 and record.memory_mb > 0
            assert record.peak_memory_mb >= record.memory_mb
            assert "SYN123" not in JsonFormatter().format(record)
            assert str(tmp_path) not in JsonFormatter().format(record)

        published = scenario == "completed"
        for table, expected_count in (
            ("enrichment_units", 1), ("enrichment_attributes", 2),
            ("enrichment_plates", 1), ("enrichment_plate_candidates", 0),
        ):
            assert jobs.connection.execute(
                f"SELECT count(*) FROM {table}"
            ).fetchone()[0] == (expected_count if published else 0)
        rows = jobs.connection.execute(
            "SELECT status, results_json FROM enrichment_jobs"
        ).fetchall()
        if published:
            assert rows[0]["status"] == "completed"
            assert "SYN123" in rows[0]["results_json"]
        elif scenario == "cancelled":
            assert rows[0]["status"] == "cancelled"
            assert rows[0]["results_json"] == "[]"
        else:
            assert not rows
            with pytest.raises(ApiError) as error:
                jobs.get(job.enrichment_job_id, "owner")
            assert error.value.status_code == 410

        job_metric = next(
            record for record in events if record.branch == "enrichment_job"
        )
        assert job_metric.status == expected_status
    finally:
        jobs.close()
