from datetime import UTC, datetime, timedelta

from app.services.temporary_artifacts import TemporaryArtifactStore


def test_rejected_upload_does_not_create_an_artifact(tmp_path):
    store = TemporaryArtifactStore(tmp_path, 20)
    assert list(tmp_path.iterdir()) == []
    assert store.get("rejected") == (None, False)


def test_expired_artifact_is_deleted(tmp_path):
    store = TemporaryArtifactStore(tmp_path, 20)
    artifact = store.save("request", b"image")
    store._artifacts["request"] = artifact.__class__("request", artifact.path, datetime.now(UTC) - timedelta(seconds=1))
    value, expired = store.get("request")
    assert value is None
    assert expired is True
    assert not artifact.path.exists()


def test_close_removes_active_artifacts(tmp_path):
    store = TemporaryArtifactStore(tmp_path, 20)
    artifact = store.save("request", b"image")
    store.close()
    assert not artifact.path.exists()
