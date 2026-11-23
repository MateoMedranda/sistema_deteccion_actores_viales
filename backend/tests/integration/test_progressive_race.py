import threading
from concurrent.futures import ThreadPoolExecutor
import pytest
from app.api.error_handlers import ApiError
from app.services.video_progressive_store import ProgressiveStore
from tests.integration.test_progressive_store import source


def test_withdrawal_serializes_with_commit_and_never_resurrects(tmp_path):
    store = ProgressiveStore(tmp_path / "db")
    source(store, tmp_path / "input")
    entered, release = threading.Event(), threading.Event()
    frame = dict(frame_index=0, start_us=0, end_us=100, pts="0", observations=[])

    def callback():
        entered.set()
        assert release.wait(3)

    with ThreadPoolExecutor(max_workers=2) as pool:
        publish = pool.submit(store.publish, "job-1", [frame], callback)
        assert entered.wait(3)
        withdraw = pool.submit(store.withdraw, "job-1", "owner")
        release.set()
        publish.result()
        withdraw.result()
    with pytest.raises(ApiError):
        store.snapshot("job-1", "owner")
    with pytest.raises(ApiError):
        store.publish("job-1", [frame])
    assert store.db.execute("SELECT count(*) FROM p_frames").fetchone()[0] == 0
    store.close()
