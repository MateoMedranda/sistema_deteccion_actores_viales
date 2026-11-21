"""Bounded RAM cache and one real CPU worker, with shared flights and no queue."""
from collections import OrderedDict
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass,field
from datetime import UTC,datetime
from threading import RLock
from time import monotonic
from uuid import uuid4
from app.api.error_handlers import ApiError
@dataclass(frozen=True)
class PreviewValue:
    png:bytes
    metadata:str
    expires_at:datetime
    @property
    def cost(self):return len(self.png)+len(self.metadata.encode("ascii"))
@dataclass
class Flight:
    key:tuple
    expires_at:datetime
    deadline:float
    consumers:set=field(default_factory=set)
    abandoned:bool=False
    future:Future=field(default_factory=Future)
    consumer_lock:object=field(default_factory=RLock)
@dataclass
class Consumer:
    flight:Flight|None
    token:str
    future:Future
class PlatePreviewStore:
    def __init__(self,*,clock=None,timer=monotonic,deadline=8.0):
        self.clock=clock or (lambda:datetime.now(UTC));self.timer=timer;self.deadline=deadline
        self.lock=RLock();self.cache=OrderedDict();self.bytes=0;self.current=None;self.closed=False
        self.executor=ThreadPoolExecutor(max_workers=1,thread_name_prefix="plate-preview")
    @property
    def busy(self):
        with self.lock:return self.current is not None
    @property
    def entry_count(self):
        with self.lock:return len(self.cache)
    @property
    def byte_count(self):
        with self.lock:return self.bytes
    def _drop(self,key):
        self.bytes-=self.cache.pop(key).cost
    def cleanup(self):
        with self.lock:
            for key,value in list(self.cache.items()):
                if value.expires_at<=self.clock():self._drop(key)
            if self.current and self.current.expires_at<=self.clock():self.current.abandoned=True
    def acquire(self,key,expires_at,compute,validate,measure=None,before_admit=None):
        with self.lock:
            self.cleanup();validate()
            if before_admit:before_admit()
            if self.closed:raise ApiError(503,"plate_preview_unavailable","Preview is unavailable.")
            if expires_at<=self.clock():raise ApiError(410,"source_expired","Evidence expired.")
            if key in self.cache:
                value=self.cache.pop(key);self.cache[key]=value
                future=Future();future.set_result(value)
                return Consumer(None,"",future)
            token=uuid4().hex
            if self.current:
                flight=self.current
                with flight.consumer_lock:
                    if flight.key!=key or flight.abandoned:raise ApiError(429,"plate_preview_busy","Preview is busy.")
                    if self.timer()>=flight.deadline:raise ApiError(504,"plate_preview_timeout","Preview timed out.")
                    flight.consumers.add(token)
            else:
                flight=Flight(key,expires_at,self.timer()+self.deadline,{token});self.current=flight
                self.executor.submit(self._run,flight,compute,validate,measure)
            return Consumer(flight,token,flight.future)
    def check(self,flight):
        with self.lock,flight.consumer_lock:
            if flight.expires_at<=self.clock():raise ApiError(410,"source_expired","Evidence expired.")
            if self.closed or flight.abandoned or not flight.consumers:raise ApiError(503,"plate_preview_unavailable","Preview was abandoned.")
            if self.timer()>=flight.deadline:raise ApiError(504,"plate_preview_timeout","Preview timed out.")
    def _run(self,flight,compute,validate,measure):
        metric=None;entered=False;exited=False
        try:
            if measure:
                metric=measure()
                if hasattr(metric,"defer_publication"):metric.defer_publication()
                metric.__enter__()
                entered=True
            value=compute(lambda:self.check(flight))
            self.check(flight)
            # Stop/sample instrumentation before evidence becomes available.
            # Real preview metrics defer emission until the publication outcome.
            if metric:
                exited=True
                metric.__exit__(None,None,None)
            with self.lock:
                self.check(flight);validate()
                with flight.consumer_lock:
                    self.check(flight)
                    if value.expires_at!=flight.expires_at or len(value.png)>2*1024*1024 or len(value.metadata.encode("ascii"))>2048:
                        raise ApiError(503,"plate_preview_unavailable","Preview is unavailable.")
                    while self.cache and (len(self.cache)>=8 or self.bytes+value.cost>16*1024*1024):
                        self._drop(next(iter(self.cache)))
                    if value.cost>16*1024*1024:raise ApiError(503,"plate_preview_unavailable","Preview is unavailable.")
                    self.cache[flight.key]=value;self.bytes+=value.cost
                    flight.future.set_result(value)
        except BaseException as exc:
            failure=exc if isinstance(exc,ApiError) else ApiError(503,"plate_preview_unavailable","Preview is unavailable.")
            if metric:
                metric.status="expired" if failure.status_code==410 else "abandoned" if flight.abandoned else "failed"
                metric.error_code=failure.code
            if not flight.future.done():flight.future.set_exception(failure)
            if metric and entered and not exited:
                exited=True
                try:metric.__exit__(type(exc),exc,exc.__traceback__)
                except BaseException:pass
        finally:
            try:
                if metric and not entered and hasattr(metric,"close_partial"):
                    try:metric.close_partial()
                    except BaseException:pass
                if metric and hasattr(metric,"publish"):
                    try:metric.publish()
                    except BaseException:pass  # A failed log sink cannot strand the CPU permit.
            finally:
                with self.lock:
                    if self.current is flight:self.current=None
    def release(self,consumer):
        # Retirement never waits for the cache/database/image locks.
        if consumer.flight:
            with consumer.flight.consumer_lock:
                consumer.flight.consumers.discard(consumer.token)
                if not consumer.flight.consumers and not consumer.future.done():consumer.flight.abandoned=True
    def close(self):
        with self.lock:
            self.closed=True;self.cache.clear();self.bytes=0
            if self.current:self.current.abandoned=True
        self.executor.shutdown(wait=False,cancel_futures=True)
