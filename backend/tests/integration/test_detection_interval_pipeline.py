import json
from types import SimpleNamespace
import pytest
from app.adapters.yolov10_tracker import YOLOv10ByteTrackAdapter
from app.services.progressive_counting import ProgressiveCountService
from tests.unit.test_detection_interval import MovingModel
from tests.integration.test_video_profile_pipeline import submit, report
from tests.integration.test_progressive_demand_count import setup, publish


@pytest.mark.parametrize("interval", [1, 2])
def test_full_video_timeline_ids_evidence_and_count_survive_interval_two(enrichment_client, tmp_path, auth_headers, monkeypatch, interval):
    client = enrichment_client
    processor = client.app.state.video_worker.processor
    model = MovingModel()
    monkeypatch.setattr(processor.detector, "create_video_tracker",
        lambda: YOLOv10ByteTrackAdapter(model, .25, "cpu"), raising=False)
    processor.detection_interval = interval
    job = submit(client, tmp_path, auth_headers)
    _, data = report(client, job)
    assert data["outcome"] == "completed"
    assert data["sampling"] == dict(requested_interval=interval, effective_interval=interval, detected_frames=12//interval, predicted_frames=12-12//interval)
    assert data["processed_frames"] == data["confirmed_frames"] == 12
    assert model.calls == list(range(0, 12, interval))
    assert data["stages"]["detection"]["calls"] == 12//interval
    assert data["stages"]["resource_wait"]["calls"] == 12//interval
    assert data["stages"]["video_write"]["calls"] == 12
    store = client.app.state.progressive_store
    with store.lock:
        frames = [json.loads(r[0]) for r in store.db.execute("SELECT payload FROM p_frames WHERE job=? ORDER BY idx", (job,))]
        evidence_indices = [r[0] for r in store.db.execute("SELECT idx FROM p_evidence WHERE job=?", (job,))]
        legacy_indices = [r[0] for r in store.db.execute("SELECT DISTINCT frame_index FROM video_detections WHERE job_id=?", (job,))]
    assert len(frames) == 12 and all(len(f["observations"]) == 2 for f in frames)
    assert all(frames[i]["end_us"] == frames[i+1]["start_us"] for i in range(11))
    identities = {}
    for frame in frames:
        for ob in frame["observations"]:
            assert identities.setdefault(ob["class_name"], ob["track_id"]) == ob["track_id"]
    assert evidence_indices and all(i % interval == 0 for i in evidence_indices)
    assert legacy_indices == list(range(0, 12, interval))
    base = f"/api/v1/video-jobs/{job}/playback"
    state = client.get(base, headers=auth_headers).json()
    response = client.get(base+"/frames", headers=auth_headers, params={"from_us":0,"to_us":frames[-1]["end_us"],"snapshot":state["revision"]})
    assert response.status_code == 200, response.text
    assert "detection_performed" not in response.text  # internal receipt, unchanged HTTP schema
    line = dict(point_a=dict(x=.4,y=0), point_b=dict(x=.4,y=1))
    count = client.put(base+"/count", headers=auth_headers, json=line)
    assert count.status_code == 200 and count.json()["total"] == 1
    assert client.get(base+"/count?at_us=0", headers=auth_headers).json()["total"] == 0
    assert client.get(base+f"/count?at_us={frames[-1]['start_us']}", headers=auth_headers).json()["total"] == 1


def test_predicted_crossing_never_counts_without_a_measurement(tmp_path):
    store, evidence = setup(tmp_path)
    publish(store, evidence, 0, 10)
    # Deliberately overestimate motion to the other side on the intermediate frame.
    frame = dict(frame_index=1, start_us=100000, end_us=200000, pts="1", detection_performed=False,
        observations=[dict(track_id=1,class_id=0,class_name="car",confidence=.9,
            raw_bbox=dict(x_min=10,y_min=70,x_max=30,y_max=80),display_bbox=None)])
    store.publish("job", [frame], on_publish=lambda:evidence.commit(SimpleNamespace(job_id="job"), [], [frame]))
    service = ProgressiveCountService(store)
    line = dict(point_a=dict(x=0,y=.5),point_b=dict(x=1,y=.5))
    assert service.configure("job","owner",line)["total"] == 0
    publish(store, evidence, 2, 10)  # real correction: vehicle never crossed
    assert service.snapshot("job","owner")["total"] == 0
    publish(store, evidence, 3, 70)  # real crossing, confirmed exactly once
    assert service.snapshot("job","owner")["total"] == 1
    assert service.snapshot("job","owner",0)["total"] == 0
    assert service.snapshot("job","owner")["total"] == 1
    store.close()


def test_unsupported_detector_falls_back_to_every_frame_and_reports_it(enrichment_client, tmp_path, auth_headers):
    client = enrichment_client
    client.app.state.video_worker.processor.detection_interval = 2
    job = submit(client, tmp_path, auth_headers)
    _, data = report(client, job)
    assert data["outcome"] == "completed"
    assert data["sampling"] == dict(requested_interval=2, effective_interval=1, detected_frames=12, predicted_frames=0)
