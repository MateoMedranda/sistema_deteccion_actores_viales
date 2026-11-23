"""Authenticated, deadline-aware file transfer with single HTTP byte ranges."""

import re
from pathlib import Path
from email.utils import formatdate
from starlette.responses import Response, StreamingResponse
from app.api.error_handlers import ApiError


def media(store, job, owner, path: Path, request, media_type="video/mp4", maximum=None):
    with store.lock:
        row = store.row(job, owner)
        if not path.is_file():
            raise ApiError(409, "source_not_ready", "The media is not available.")
        size = path.stat().st_size
        if maximum and size > maximum:
            raise ApiError(422, "evidence_too_large", "The media is unavailable.")
        etag = '"' + row["generation"] + "-" + str(size) + '"'
        headers = {
            "Accept-Ranges": "bytes",
            "Cache-Control": "no-store",
            "Cross-Origin-Resource-Policy": "same-origin",
            "ETag": etag,
            "Last-Modified": formatdate(path.stat().st_mtime, usegmt=True),
        }
        start, end = 0, size - 1
        status = 200
        value = request.headers.get("range") if request.method != "HEAD" else None
        if value and request.headers.get("if-range", etag) == etag:
            m = re.fullmatch(r"bytes=(\d{1,20})-(\d{0,20})|bytes=-(\d{1,20})", value)
            if m:
                if m[3]:
                    suffix = int(m[3])
                    start = max(0, size - suffix)
                    if suffix == 0:
                        m = None
                else:
                    start = int(m[1])
                    end = min(size - 1, int(m[2]) if m[2] else size - 1)
            if not m or start >= size or end < start:
                return Response(
                    status_code=416, headers={**headers, "Content-Range": f"bytes */{size}"}
                )
            status = 206
            headers["Content-Range"] = f"bytes {start}-{end}/{size}"
        if request.method == "HEAD":
            headers["Content-Length"] = str(max(0, end - start + 1))
            return Response(headers=headers, media_type=media_type)
        handle = path.open("rb")
        handle.seek(start)
        key = str(path)
        store.readers[key] = store.readers.get(key, 0) + 1

    def stream():
        remaining = end - start + 1
        try:
            while remaining:
                try:
                    with store.lock:
                        store.row(job, owner)
                except ApiError:
                    return
                block = handle.read(min(65536, remaining))
                if not block:
                    break
                remaining -= len(block)
                yield block
        finally:
            handle.close()
            with store.lock:
                store.readers[key] -= 1
                if not store.readers[key]:
                    del store.readers[key]

    return StreamingResponse(stream(), status_code=status, headers=headers, media_type=media_type)
