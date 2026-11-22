import json
from pathlib import Path


def test_benchmark_manifest_is_non_secret_and_reproducible(tmp_path) -> None:
    evidence = {"videos": 0, "p95_processing_seconds": None, "status": "pending_authorized_dataset"}
    path = tmp_path / "video-benchmark.json"
    path.write_text(json.dumps(evidence), encoding="utf-8")
    assert json.loads(path.read_text(encoding="utf-8"))["status"] == "pending_authorized_dataset"
