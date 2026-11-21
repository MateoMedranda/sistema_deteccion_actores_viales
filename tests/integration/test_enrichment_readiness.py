import numpy as np
import pytest
from app.services.enrichment_processing import EnrichmentProcessor
from tests.enrichment_fixtures import FakeAttributes, FakeLocalizer, FakeReader
from tests.conftest import image_bytes

def submit(client, auth_headers):
    return client.post("/api/v1/detections/images",headers=auth_headers,
        files={"image":("scene.jpg",image_bytes(),"image/jpeg")}).json()["request_id"]

def test_unconfigured_models_are_not_ready_and_do_not_accept_jobs(client,auth_headers):
    ready=client.get("/health/enrichment-ready")
    assert ready.status_code==503
    assert set(ready.json()["capabilities"].values())=={"unavailable"}
    source=submit(client,auth_headers)
    response=client.post("/api/v1/enrichment-jobs",headers=auth_headers,json={"source":{"kind":"image","source_id":source}})
    assert response.status_code==503 and response.json()["code"]=="enrichment_unavailable"

def test_configured_test_adapters_are_actually_ready(enrichment_client):
    response=enrichment_client.get("/health/enrichment-ready")
    assert response.status_code==200
    assert set(response.json()["capabilities"].values())=={"ready"}

@pytest.mark.parametrize("attributes,localizer,reader",[
    (True,False,False),(False,True,False),(False,True,True),(True,True,True)])
def test_useful_independent_branches_accept_work(client,auth_headers,attributes,localizer,reader):
    processor=EnrichmentProcessor(FakeAttributes() if attributes else None,FakeLocalizer() if localizer else None,
        FakeReader() if reader else None,.7,.8)
    client.app.state.enrichment_job_service.processor=processor
    client.app.state.enrichment_worker.processor=processor
    source=submit(client,auth_headers)
    ready=client.get("/health/enrichment-ready")
    assert ready.status_code==(200 if attributes and localizer and reader else 503)
    accepted=client.post("/api/v1/enrichment-jobs",headers=auth_headers,json={"source":{"kind":"image","source_id":source}})
    assert accepted.status_code==202

def test_localization_survives_missing_reader():
    attrs,plate=EnrichmentProcessor(None,FakeLocalizer(),None,.7,.8).enrich(np.zeros((20,30,3),dtype=np.uint8))
    assert attrs["status"]=="failed"
    assert plate["status"]=="failed" and plate["error_code"]=="plate_reader_unavailable"
    assert plate["bbox_relative"]["x_min"]==pytest.approx(2/30)

def test_source_owner_is_validated_before_model_availability(client,auth_headers):
    response=client.post("/api/v1/enrichment-jobs",headers=auth_headers,json={"source":{"kind":"image","source_id":"unknown"}})
    assert response.status_code==404
