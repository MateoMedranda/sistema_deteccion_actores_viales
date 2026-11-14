from __future__ import annotations


def test_count_jobs_openapi_exposes_cancel_operation(client) -> None:
    operation = client.get("/openapi.json").json()["paths"]["/api/v1/count-jobs/{countJobId}"]["delete"]
    assert operation["responses"]["202"]["description"]
    assert "CountJobResponse" in str(operation)
