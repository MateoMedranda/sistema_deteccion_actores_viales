"""Owner-scoped intent keys; no raw key or vehicle data is retained."""
import hashlib,re,json
from app.api.error_handlers import ApiError
def key_hash(value):
    if value is None:return None
    if not re.fullmatch(r"[A-Za-z0-9_-]{16,128}",value):raise ApiError(422,"invalid_idempotency_key","The idempotency header is invalid.")
    return hashlib.sha256(value.encode("ascii")).hexdigest()
def source_fingerprint(kind,source_id):
    return hashlib.sha256(json.dumps({"kind":kind,"source_id":source_id},sort_keys=True,separators=(",",":")).encode()).hexdigest()
