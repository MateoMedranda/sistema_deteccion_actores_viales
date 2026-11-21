import time
from datetime import UTC,datetime,timedelta
from threading import Event
from concurrent.futures import ThreadPoolExecutor
import pytest
from app.api.error_handlers import ApiError
from app.services.plate_preview_store import PlatePreviewStore,PreviewValue
def test_deadline_is_shared_and_late_worker_keeps_single_cpu_slot():
    timer=[0.];gate=Event();started=Event();expiry=datetime.now(UTC)+timedelta(seconds=30)
    store=PlatePreviewStore(timer=lambda:timer[0]);calls=[]
    def compute(check):calls.append(1);started.set();gate.wait(2);check();return PreviewValue(b"png","{}",expiry)
    a=store.acquire((1,),expiry,compute,lambda:None);assert started.wait(1)
    timer[0]=7;b=store.acquire((1,),expiry,compute,lambda:None)
    assert a.flight.deadline==b.flight.deadline==8
    timer[0]=8
    with pytest.raises(ApiError) as timeout:store.check(a.flight)
    assert timeout.value.status_code==504
    store.release(a);store.release(b)
    with pytest.raises(ApiError) as busy:store.acquire((2,),expiry,compute,lambda:None)
    assert busy.value.status_code==429 and store.busy
    gate.set()
    with pytest.raises(ApiError):a.future.result(2)
    store.close()
    assert len(calls)==1 and store.entry_count==0
def test_simultaneous_consumers_share_one_result_but_hits_validate_again():
    gate=Event();started=Event();expiry=datetime.now(UTC)+timedelta(seconds=30);store=PlatePreviewStore();calls=[]
    def compute(check):calls.append(1);started.set();gate.wait(2);check();return PreviewValue(b"png","{}",expiry)
    a=store.acquire((1,),expiry,compute,lambda:None);assert started.wait(1)
    b=store.acquire((1,),expiry,compute,lambda:None);gate.set()
    assert a.future.result(2) is b.future.result(2)
    store.release(a);store.release(b)
    def denied():raise ApiError(410,"source_expired","safe")
    with pytest.raises(ApiError):store.acquire((1,),expiry,compute,denied)
    store.close();assert len(calls)==1
def test_expiry_during_worker_prevents_cache_and_close_removes_memory():
    clock=[datetime.now(UTC)];expiry=clock[0]+timedelta(seconds=1);gate=Event()
    store=PlatePreviewStore(clock=lambda:clock[0])
    def compute(check):gate.wait(2);check();return PreviewValue(b"png","{}",expiry)
    c=store.acquire((1,),expiry,compute,lambda:None)
    clock[0]=expiry;gate.set()
    with pytest.raises(ApiError):c.future.result(2)
    store.close();assert store.byte_count==0
