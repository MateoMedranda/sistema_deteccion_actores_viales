import pytest
from app.api.error_handlers import ApiError
from app.services.video_job_store import VideoJobStore
from app.services.enrichment_job_store import EnrichmentJobStore
from tests.unit.test_video_job_store import metadata
from tests.fixtures_008 import Clock
def test_owner_scoped_replay_conflict_and_original_expiry(tmp_path):
 clock=Clock();s=VideoJobStore(tmp_path/"video.db",60,5,clock=clock)
 a=s.create("a",metadata(),tmp_path/"a",idempotency_key_hash="hash",request_fingerprint="fp")
 clock.advance(5);b=s.create("a",metadata(),tmp_path/"extra",idempotency_key_hash="hash",request_fingerprint="fp")
 assert a.job_id==b.job_id and a.expires_at==b.expires_at
 with pytest.raises(ApiError) as e:s.create("a",metadata(),tmp_path/"bad",idempotency_key_hash="hash",request_fingerprint="other")
 assert e.value.status_code==409
 assert s.create("b",metadata(),tmp_path/"b",idempotency_key_hash="hash",request_fingerprint="fp").job_id!=a.job_id
 s.close()
def test_enrichment_replay_does_not_create_another_job(tmp_path):
 clock=Clock();s=EnrichmentJobStore(tmp_path/"enrich.db",60,5,clock=clock);from datetime import timedelta
 args=("video","source","owner",1,clock()+timedelta(seconds=120))
 a=s.create(*args,idempotency_key_hash="hash",request_fingerprint="fp");clock.advance(5)
 b=s.create(*args,idempotency_key_hash="hash",request_fingerprint="fp")
 assert a.enrichment_job_id==b.enrichment_job_id and a.expires_at==b.expires_at
 s.close()
