from datetime import datetime, UTC, timedelta
import json
from fastapi.testclient import TestClient
from app.main import create_app
from tests.conftest import isolated_settings, FakeDetector


def test_all_progressive_resources_are_owner_scoped_and_hide_storage_paths(tmp_path):
    settings = isolated_settings(tmp_path, api_keys="alice:key-a,bob:key-b", api_key=None)
    with TestClient(create_app(settings, FakeDetector())) as client:
        client.app.state.video_worker.close()
        store = client.app.state.progressive_store
        path = tmp_path / "private-original.mp4"
        path.write_bytes(b"original")
        store.create(
            "owned",
            "alice",
            path,
            dict(width=64, height=48, fps=10, duration=1),
            datetime.now(UTC) + timedelta(minutes=2),
        )
        store.publish(
            "owned", [dict(frame_index=0, start_us=0, end_us=100000, pts="0", observations=[])]
        )
        base = "/api/v1/video-jobs/owned/playback"
        for method, suffix in (
            ("GET", ""),
            ("DELETE", ""),
            ("GET", "/source"),
            ("HEAD", "/source"),
            ("GET", "/frames?from_us=0&to_us=100000&snapshot=1"),
            ("GET", "/tracks?snapshot=0"),
            ("GET", "/tracks/1"),
            ("GET", "/tracks/1/evidence/12345678-1234-1234-1234-123456789012/vehicle"),
        ):
            response = client.request(method, base + suffix, headers={"X-API-Key": "key-b"})
            assert response.status_code == 404, (method, suffix, response.text)
            assert str(tmp_path) not in response.text
        response = client.get(base, headers={"X-API-Key": "key-a"})
        assert response.status_code == 200
        assert str(tmp_path) not in response.text and "private-original" not in response.text
        for q in (
            "from_us=0&to_us=1&snapshot=0&snapshot=1",
            "from_us=0&to_us=30000001&snapshot=1",
            "from_us=0&to_us=1&snapshot=9007199254740992",
        ):
            assert client.get(
                base + "/frames?" + q, headers={"X-API-Key": "key-a"}
            ).status_code in (409, 422)
