from typing import Literal
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Request, Response, Path as PathParam
from app.api.dependencies import Principal, require_api_key
from app.api.error_handlers import ApiError
from app.domain.progressive import PlaybackState, FramePage, TrackPage, TrackResult
from app.services.progressive_media import media
from app.domain.progressive_count import CountLine, ProgressiveCountState

router = APIRouter(prefix="/v1/video-jobs", tags=["progressive-video"])


def query(request, allowed):
    keys = [k for k, v in request.query_params.multi_items()]
    if len(keys) != len(set(keys)) or set(keys) - set(allowed):
        raise ApiError(422, "query_invalid", "Invalid query.")


@router.get("/{job_id}/playback", response_model=PlaybackState)
def state(job_id: str, request: Request, principal: Principal = Depends(require_api_key)):
    query(request, [])
    return request.app.state.progressive.snapshot(job_id, principal.key_id)


@router.delete("/{job_id}/playback", status_code=204)
def withdraw(job_id: str, request: Request, principal: Principal = Depends(require_api_key)):
    query(request, [])
    request.app.state.progressive.withdraw(job_id, principal.key_id)
    return Response(status_code=204)


@router.get("/{job_id}/playback/source")
@router.head("/{job_id}/playback/source")
def source(job_id: str, request: Request, principal: Principal = Depends(require_api_key)):
    query(request, [])
    store = request.app.state.progressive_store
    with store.lock:
        row = store.row(job_id, principal.key_id)
        if not row["frames"]:
            raise ApiError(409, "source_not_ready", "The source is not ready.")
        path = __import__("pathlib").Path(row["source"])
    return media(store, job_id, principal.key_id, path, request)


@router.get("/{job_id}/playback/frames", response_model=FramePage)
def frames(
    job_id: str,
    request: Request,
    from_us: int = Query(ge=0, le=9007199254740991),
    to_us: int = Query(gt=0, le=9007199254740991),
    snapshot: int = Query(ge=0, le=9007199254740991),
    cursor: str | None = Query(default=None, max_length=512),
    principal: Principal = Depends(require_api_key),
):
    query(request, ["from_us", "to_us", "snapshot", "cursor"])
    return request.app.state.progressive.frames(
        job_id, principal.key_id, from_us, to_us, snapshot, cursor
    )


@router.get("/{job_id}/playback/tracks", response_model=TrackPage)
def tracks(
    job_id: str,
    request: Request,
    snapshot: int = Query(ge=0, le=9007199254740991),
    cursor: str | None = Query(default=None, max_length=512),
    principal: Principal = Depends(require_api_key),
):
    query(request, ["snapshot", "cursor"])
    return request.app.state.progressive_evidence.tracks(job_id, principal.key_id, snapshot, cursor)


@router.get("/{job_id}/playback/tracks/{track_id}", response_model=TrackResult)
def track(
    job_id: str,
    request: Request,
    track_id: int = PathParam(ge=1, le=9007199254740991),
    principal: Principal = Depends(require_api_key),
):
    query(request, [])
    return request.app.state.progressive_evidence.track(job_id, principal.key_id, track_id)


@router.get("/{job_id}/playback/tracks/{track_id}/evidence/{evidence_id}/{kind}")
def evidence(
    job_id: str,
    evidence_id: UUID,
    kind: Literal["vehicle", "plate"],
    request: Request,
    track_id: int = PathParam(ge=1, le=9007199254740991),
    principal: Principal = Depends(require_api_key),
):
    query(request, [])
    path = request.app.state.progressive_evidence.resource(
        job_id, principal.key_id, track_id, str(evidence_id), kind
    )
    return media(
        request.app.state.progressive_store,
        job_id,
        principal.key_id,
        path,
        request,
        "image/png",
        16 * 1024**2,
    )


@router.post("/{job_id}/playback/tracks/{track_id}/enrich", status_code=202, response_model=TrackResult)
def enrich_track(job_id: str, request: Request, track_id: int = PathParam(ge=1,le=9007199254740991), principal: Principal = Depends(require_api_key)):
    query(request, [])
    return request.app.state.progressive_evidence.request(job_id,principal.key_id,track_id)


@router.put("/{job_id}/playback/count", response_model=ProgressiveCountState)
def configure_count(job_id: str, body: CountLine, request: Request, principal: Principal = Depends(require_api_key)):
    query(request, [])
    return request.app.state.progressive_count.configure(job_id,principal.key_id,body.model_dump())

@router.get("/{job_id}/playback/count", response_model=ProgressiveCountState)
def get_count(job_id: str, request: Request, at_us: int = Query(default=0,ge=0,le=9007199254740991), principal: Principal = Depends(require_api_key)):
    query(request, ["at_us"])
    return request.app.state.progressive_count.snapshot(job_id,principal.key_id,at_us)

@router.delete("/{job_id}/playback/count", status_code=204)
def disable_count(job_id: str, request: Request, principal: Principal = Depends(require_api_key)):
    query(request, [])
    request.app.state.progressive_count.disable(job_id,principal.key_id)
    return Response(status_code=204)
