import importlib.util
import json
from pathlib import Path
import time
from tests.fixtures_progressive import video


def submit(client, tmp_path, headers):
    source = video(tmp_path / "profile-sample.mp4")
    response = client.post("/api/v1/video-jobs?presentation=progressive&enrichment=on-demand",
        headers=headers, files={"video": ("PRIVATE_SOURCE.mp4", source.read_bytes(), "video/mp4")})
    assert response.status_code == 202
    return response.json()["job_id"]


def report(client, job_id):
    root = client.app.state.video_worker.processor.profile_root
    path = root / (job_id + ".json")
    end = time.monotonic() + 12
    while time.monotonic() < end:
        if path.exists():
            data = json.loads(path.read_text())
            if data["outcome"] != "processing":
                return path, data
        time.sleep(.02)
    raise AssertionError("No terminal profile saved")


def test_normal_video_report_and_cli_are_local_and_preserve_pipeline(enrichment_client, tmp_path, auth_headers, capsys):
    client = enrichment_client
    job_id = submit(client, tmp_path, auth_headers)
    path, data = report(client, job_id)
    assert data["outcome"] == "completed" and data["analysis_complete"]
    assert data["processed_frames"] == data["confirmed_frames"] == 12
    assert data["analysis_fps"] > 0 and data["analysis_wall_ms"] > 0
    stages = data["stages"]
    assert stages["detection"]["calls"] == stages["tracking"]["calls"] == 12
    assert stages["video_write"]["calls"] == stages["annotation"]["calls"] == 0
    assert stages["publication"]["calls"] >= 1 and stages["final_encode"]["calls"] == 0
    assert stages["resource_wait"]["calls"] == 12
    assert data["first_publication_ms"] is not None
    assert data["initial_buffer_available_ms"] is None  # synthetic clip is shorter than the buffer
    assert "PRIVATE_SOURCE" not in path.read_text() and str(tmp_path) not in path.read_text()
    assert "owner_key_id" not in data and "api_key" not in data and "plate" not in data
    script = Path(__file__).resolve().parents[2] / "scripts" / "report_video_profile.py"
    spec = importlib.util.spec_from_file_location("profile_cli", script)
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    assert cli.main(["--latest", "--directory", str(path.parent)]) == 0
    assert "FPS efectivos" in capsys.readouterr().out
    assert cli.main(["--job", job_id, "--directory", str(path.parent), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["job_id"] == job_id


def test_failure_before_first_published_batch_still_produces_diagnostic(enrichment_client, tmp_path, auth_headers, monkeypatch):
    client = enrichment_client
    def fail(*args):
        raise RuntimeError("PRIVATE_PATH_SECRET")
    monkeypatch.setattr(client.app.state.video_worker.processor.detector, "detect", fail)
    job_id = submit(client, tmp_path, auth_headers)
    _, data = report(client, job_id)
    assert data["outcome"] == "failed" and not data["analysis_complete"]
    assert data["processed_frames"] == data["confirmed_frames"] == 0
    assert data["stages"]["detection"]["calls"] == 1
    assert data["stages"]["final_encode"]["calls"] == 0
    assert data["error_code"] == "processing_failed"
    assert "PRIVATE_PATH_SECRET" not in json.dumps(data)


def test_unwritable_profile_directory_does_not_fail_video(enrichment_client, tmp_path, auth_headers):
    client = enrichment_client
    blocked = tmp_path / "not-a-directory"
    blocked.write_text("existing file")
    client.app.state.video_worker.processor.profile_root = blocked
    job_id = submit(client, tmp_path, auth_headers)
    end = time.monotonic() + 12
    while time.monotonic() < end:
        state = client.get("/api/v1/video-jobs/" + job_id, headers=auth_headers).json()
        if state["status"] in ("completed", "failed"):
            break
        time.sleep(.02)
    assert state["status"] == "completed"


def test_export_failure_does_not_mix_export_duration_into_analysis(enrichment_client, tmp_path, auth_headers, monkeypatch):
    from app.services.video_processing import VideoProcessingError
    client = enrichment_client
    def fail_encode(*args, **kwargs):
        raise VideoProcessingError("video_encoding_failed")
    monkeypatch.setattr(client.app.state.video_worker.processor, "_encode_h264", fail_encode)
    job_id = submit(client, tmp_path, auth_headers)
    _, data = report(client, job_id)
    assert data["outcome"] == "completed" and data["analysis_complete"]
    assert data["confirmed_frames"] == data["processed_frames"] == 12
    assert data["error_code"] is None
    assert data["stages"]["final_encode"]["calls"] == 0
    assert data["stages"]["final_encode"]["analysis_percent"] is None
    assert data["total_wall_ms"] >= data["analysis_wall_ms"]
