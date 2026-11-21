from dataclasses import replace
from datetime import UTC, datetime, timedelta
from io import BytesIO
from PIL import Image, ImageOps
import pytest
from tests.image_exploration_fixtures import scene_bytes
from tests.conftest import image_bytes

@pytest.mark.parametrize("orientation", range(1, 9))
def test_exif_dimensions_original_and_boxes_use_identical_space(client, auth_headers, orientation):
    data = scene_bytes(orientation, (80, 40))
    response = client.post("/api/v1/detections/images", headers=auth_headers,
                           files={"image": ("scene.jpg", data, "image/jpeg")})
    assert response.status_code == 200
    result = response.json()
    expected = ImageOps.exif_transpose(Image.open(BytesIO(data))).convert("RGB")
    assert (result["image"]["width"], result["image"]["height"]) == expected.size
    assert result["image"]["media_type"] == "image/png"
    assert result["source_expires_at"] == result["original_image"]["expires_at"]
    original = client.get(result["original_image"]["url"], headers=auth_headers)
    assert original.status_code == 200 and original.headers["cache-control"] == "no-store"
    canonical = Image.open(BytesIO(original.content))
    assert canonical.size == expected.size and canonical.getexif().get(274) is None
    assert canonical.tobytes() == expected.tobytes()

def test_original_requires_owner_and_expires_without_leaking_identity(client, auth_headers):
    result = client.post("/api/v1/detections/images", headers=auth_headers,
                         files={"image": ("image.jpg", image_bytes(), "image/jpeg")}).json()
    source_id = result["request_id"]
    url = result["original_image"]["url"]
    assert client.get(url).status_code == 401
    store = client.app.state.image_sources
    owner = store._sources[source_id].owner_key_id
    store._sources[source_id] = replace(store._sources[source_id], owner_key_id="different-owner")
    assert client.get(url, headers=auth_headers).status_code == 404
    store._sources[source_id] = replace(store._sources[source_id], owner_key_id=owner,
                                       expires_at=datetime.now(UTC)-timedelta(seconds=1))
    assert client.get(url, headers=auth_headers).status_code == 410
    assert client.get("/api/v1/detections/missing/original-image", headers=auth_headers).status_code == 404

def test_eligibility_comes_from_server_configuration(client, auth_headers):
    client.app.state.settings.vehicle_classes = "bus"
    body = client.post("/api/v1/detections/images", headers=auth_headers,
                       files={"image": ("image.jpg", image_bytes(), "image/jpeg")}).json()
    assert body["detections"][0]["enrichment_eligible"] is False
