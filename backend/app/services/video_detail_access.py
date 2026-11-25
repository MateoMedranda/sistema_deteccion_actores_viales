"""Parent authority and reader leases shared by additive detail services."""
from contextlib import contextmanager
from app.api.error_handlers import ApiError

def parent(store,job,owner,generation=None):
 row=store.row(job,owner)
 if generation is not None and str(generation)!=row['generation']:raise ApiError(409,'generation_changed','The generation changed.')
 return row

@contextmanager
def reader_lease(store,job,owner,path):
 key=str(path)
 with store.lock:
  parent(store,job,owner);store.readers[key]=store.readers.get(key,0)+1
 try:yield
 finally:
  with store.lock:
   store.readers[key]-=1
   if not store.readers[key]:del store.readers[key]
