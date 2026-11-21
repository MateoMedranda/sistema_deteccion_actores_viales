import time
from datetime import UTC,datetime,timedelta
from threading import Event
import pytest
from app.services.plate_preview_store import PlatePreviewStore, PreviewValue
from app.api.error_handlers import ApiError
def value(expires):
    return PreviewValue(b"png", "{}", expires)
def test_singleflight_busy_abandoned_and_real_permit():
    store=PlatePreviewStore(deadline=.05);gate=Event();started=Event();calls=[]
    expiry=datetime.now(UTC)+timedelta(seconds=30)
    def compute(check):calls.append(1);started.set();gate.wait(2);check();return value(expiry)
    key=("owner","source","job",1,"display-contrast-v1")
    a=store.acquire(key,expiry,compute,lambda:None);assert started.wait(1)
    b=store.acquire(key,expiry,compute,lambda:None);assert a.flight is b.flight
    with pytest.raises(ApiError) as e:store.acquire(("other",),expiry,compute,lambda:None)
    assert e.value.status_code==429
    store.release(a);store.release(b)
    assert store.busy
    gate.set()
    for _ in range(100):
        if not store.busy:break
        time.sleep(.01)
    assert not store.busy and store.entry_count==0 and len(calls)==1
    store.close()
def test_cache_lru_absolute_expiry_and_close():
    clock=[datetime.now(UTC)]
    store=PlatePreviewStore(clock=lambda:clock[0]);expiry=clock[0]+timedelta(seconds=5)
    for n in range(10):
        token=store.acquire((n,),expiry,lambda check:value(expiry),lambda:None)
        token.future.result(2);store.release(token)
    assert store.entry_count==8
    clock[0]+=timedelta(seconds=5);store.cleanup()
    assert store.entry_count==0 and store.byte_count==0
    store.close()
