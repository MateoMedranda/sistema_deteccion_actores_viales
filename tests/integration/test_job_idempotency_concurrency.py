from concurrent.futures import ThreadPoolExecutor
from tests.unit.test_video_job_store import metadata
from app.services.video_job_store import VideoJobStore
def test_concurrent_identical_intents_admit_one_row(tmp_path):
 store=VideoJobStore(tmp_path/"jobs.db",60,20)
 def submit(i):return store.create("owner",metadata(),tmp_path/str(i),idempotency_key_hash="hash",request_fingerprint="same").job_id
 with ThreadPoolExecutor(max_workers=8) as pool:ids=list(pool.map(submit,range(8)))
 assert len(set(ids))==1
 assert store._connection.execute("SELECT count(*) FROM video_jobs").fetchone()[0]==1
 assert store.dequeue() is not None and store.dequeue() is None
 store.close()
