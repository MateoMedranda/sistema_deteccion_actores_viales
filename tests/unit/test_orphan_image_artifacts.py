from datetime import UTC,datetime,timedelta
from pathlib import Path
from app.services.source_artifacts import SourceArtifactStore
from app.services.temporary_artifacts import TemporaryArtifactStore
from app.services.image_detection_store import ImageDetectionStore

def test_reinitialized_source_store_cleans_expired_own_files_and_preserves_foreign(tmp_path):
    clock=[datetime.now(UTC)]
    artifacts=SourceArtifactStore(tmp_path)
    sources=ImageDetectionStore(artifacts,1,clock=lambda:clock[0])
    source=sources.create("source","owner",b"pixels","image/png",1,1,[])
    foreign=tmp_path/"user-note.txt";foreign.write_text("keep")
    clock[0]+=timedelta(seconds=2)
    restarted=ImageDetectionStore(SourceArtifactStore(tmp_path),1,clock=lambda:clock[0])
    restarted.cleanup()
    assert not source.original_path.exists()
    assert foreign.read_text()=="keep"

def test_reinitialized_annotations_keep_deadline_and_delete_only_owned_files(tmp_path):
    clock=[datetime.now(UTC)]
    first=TemporaryArtifactStore(tmp_path,10,clock=lambda:clock[0])
    artifact=first.save("request",b"pixels","owner")
    foreign=tmp_path/"keep.jpg";foreign.write_bytes(b"foreign")
    clock[0]+=timedelta(seconds=5)
    second=TemporaryArtifactStore(tmp_path,10,clock=lambda:clock[0])
    second.cleanup()
    assert artifact.path.exists()
    clock[0]+=timedelta(seconds=6)
    second.cleanup()
    assert not artifact.path.exists()
    assert foreign.read_bytes()==b"foreign"

def test_published_shorter_expiry_remains_effective_after_restart(tmp_path):
    clock=[datetime.now(UTC)]
    sources=ImageDetectionStore(SourceArtifactStore(tmp_path),100,clock=lambda:clock[0])
    source=sources.create("source","owner",b"pixels","image/png",1,1,[])
    sources.limit_expiry(source.source_id,clock[0]+timedelta(seconds=1))
    clock[0]+=timedelta(seconds=2)
    restarted=ImageDetectionStore(SourceArtifactStore(tmp_path),100,clock=lambda:clock[0])
    restarted.cleanup()
    assert not source.original_path.exists()
