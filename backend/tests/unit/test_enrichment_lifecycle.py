from datetime import UTC, datetime, timedelta
from threading import Barrier, Thread
import pytest
from app.services.enrichment_job_store import EnrichmentJobStore
from app.api.error_handlers import ApiError
from tests.unit.test_enrichment_results import result

def make_store(tmp_path):
    clock=[datetime.now(UTC)]
    store=EnrichmentJobStore(tmp_path/"jobs.sqlite3",60,5,clock=lambda:clock[0])
    job=store.create("image","source","owner",1,clock[0]+timedelta(seconds=5))
    store.dequeue()
    return store,job,clock

@pytest.mark.parametrize("terminal",["cancel","fail"])
def test_terminal_status_cannot_be_overwritten_by_finish(tmp_path,terminal):
    store,job,clock=make_store(tmp_path)
    if terminal=="cancel": store.cancel(job.enrichment_job_id,"owner")
    else: store.fail(job.enrichment_job_id,"processing_failed")
    store.finish(job.enrichment_job_id,[result()])
    assert store.get(job.enrichment_job_id,"owner").status.value==("cancelled" if terminal=="cancel" else "failed")
    assert store.connection.execute("SELECT results_json FROM enrichment_jobs").fetchone()[0]=="[]"
    store.close()

def test_expired_results_are_purged_even_if_finish_arrives(tmp_path):
    store,job,clock=make_store(tmp_path)
    clock[0]+=timedelta(seconds=6)
    store.finish(job.enrichment_job_id,[result()])
    store.cleanup()
    assert store.connection.execute("SELECT count(*) FROM enrichment_jobs").fetchone()[0]==0
    assert store.connection.execute("SELECT count(*) FROM enrichment_plates").fetchone()[0]==0
    with pytest.raises(ApiError) as error: store.get(job.enrichment_job_id,"owner")
    assert error.value.status_code==410
    with pytest.raises(ApiError) as error: store.get(job.enrichment_job_id,"other")
    assert error.value.status_code==404
    store.close()

def test_cancel_finish_race_has_one_atomic_winner(tmp_path):
    store,job,clock=make_store(tmp_path)
    gate=Barrier(2)
    errors=[]
    def cancel():
        gate.wait()
        try: store.cancel(job.enrichment_job_id,"owner")
        except ApiError as exc: errors.append(exc.status_code)
    thread=Thread(target=cancel)
    thread.start(); gate.wait()
    store.finish(job.enrichment_job_id,[result()])
    thread.join()
    state=store.get(job.enrichment_job_id,"owner").status.value
    assert state in {"completed","cancelled"}
    assert errors==([409] if state=="completed" else [])
    if state=="cancelled":
        assert store.connection.execute("SELECT count(*) FROM enrichment_units").fetchone()[0]==0
    store.close()

def test_processing_has_no_partial_results_and_progress_is_bounded(tmp_path):
    store,job,clock=make_store(tmp_path)
    store.progress(job.enrichment_job_id,999)
    assert store.get(job.enrichment_job_id,"owner").processed_units==1
    assert store.results(job.enrichment_job_id,"owner",1,50)==([],0)
    store.finish(job.enrichment_job_id,[result()])
    assert store.results(job.enrichment_job_id,"owner",1,50)[1]==1
    store.close()
