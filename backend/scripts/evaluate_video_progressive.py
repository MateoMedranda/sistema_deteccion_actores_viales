"""Private isolated AB/BA evaluator. Never writes media, paths or predictions to its report."""

from __future__ import annotations
import argparse, asyncio, hashlib, json, os, subprocess, sys, time, zipfile, io
from pathlib import Path

REFERENCE = "431b6dfccea3fcaccf80feab9039c254604c0718"


def code_hash(root):
    digest = hashlib.sha256()
    for path in sorted((root / "backend/app").rglob("*.py")):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def compare_quality(runtime, pair):
    import sqlite3

    left = sqlite3.connect(runtime / f"pair-{pair}-legacy" / "video.sqlite3")
    right = sqlite3.connect(runtime / f"pair-{pair}-progressive" / "video.sqlite3")
    query = "SELECT frame_index,track_id,class_id,class_name,confidence,x_min,y_min,x_max,y_max FROM video_detections ORDER BY frame_index,track_id,class_id"
    a, b = left.execute(query).fetchall(), right.execute(query).fetchall()
    left_by={row[:4]:row for row in a};right_by={row[:4]:row for row in b}
    common_keys=set(left_by)&set(right_by)
    missing=set(left_by)-set(right_by);extra=set(right_by)-set(left_by)
    box_changes=[key for key in common_keys if left_by[key][5:]!=right_by[key][5:]]
    changed=[*missing,*extra,*box_changes]
    result=dict(legacy_observations=len(a),progressive_observations=len(b),
        missing_observations=len(missing),extra_observations=len(extra),
        identity_class_mismatches=len(missing)+len(extra),bbox_mismatches=len(box_changes),
        first_changed_frame=min((key[0] for key in changed),default=None),
        max_confidence_delta=max((abs(left_by[key][4]-right_by[key][4]) for key in common_keys),default=0))
    old = sqlite3.connect(runtime / f"pair-{pair}-legacy" / "enrich.sqlite3")
    old_units = {
        u["track_id"]: u
        for row in old.execute("SELECT results_json FROM enrichment_jobs WHERE status='completed'")
        for u in json.loads(row[0])
    }
    new_units = {
        json.loads(row[0])["track_id"]: json.loads(row[0])
        for row in right.execute("SELECT payload FROM p_tracks")
    }
    common = set(old_units) & set(new_units)
    result.update(
        legacy_units=len(old_units),
        progressive_units=len(new_units),
        final_unit_identity_match=set(old_units) == set(new_units),
        final_plate_text_mismatches=sum(
            (old_units[t].get("plate") or {}).get("text") != new_units[t]["plate"]["text"]
            for t in common
        ),
        final_evidence_mismatches=sum(
            old_units[t]["evidence_frame_indexes"]
            != [e["frame_index"] for e in new_units[t]["evidence"]]
            for t in common
        ),
    )
    left.close()
    right.close()
    old.close()
    return result


def arguments():
    p = argparse.ArgumentParser()
    p.add_argument("--video", required=True, type=Path)
    p.add_argument("--runtime", required=True, type=Path)
    p.add_argument("--env", required=True, type=Path)
    p.add_argument("--timeout", type=int, default=1800)
    p.add_argument("--child", choices=["legacy", "progressive"])
    p.add_argument("--code", type=Path)
    return p.parse_args()


async def child(a):
    sys.path.insert(0, str(a.code / "backend"))
    os.chdir(a.code / "backend")
    from fastapi import UploadFile
    from starlette.datastructures import Headers
    from app.core.config import Settings
    from app.main import create_app
    from app.api.dependencies import Principal
    from app.domain.models import VideoJobStatus

    s = Settings(
        _env_file=a.env,
        api_key="isolated-benchmark-key",
        video_job_timeout_seconds=a.timeout,
        video_result_ttl_seconds=7200,
        max_video_upload_bytes=512 * 1024**2,
        max_video_duration_seconds=301,
        max_video_frames=10000,
        temp_artifact_dir=a.runtime / "images",
        video_job_db_path=a.runtime / "video.sqlite3",
        video_temp_dir=a.runtime / "video",
        count_job_db_path=a.runtime / "count.sqlite3",
        count_temp_dir=a.runtime / "count",
        enrichment_job_db_path=a.runtime / "enrich.sqlite3",
        enrichment_temp_dir=a.runtime / "enrich",
    )
    fingerprint = code_hash(a.code)
    app = create_app(s)
    async with app.router.lifespan_context(app):
        import logging

        logging.getLogger("road_actor_detection").setLevel(logging.ERROR)
        if not app.state.ready:
            raise RuntimeError("models_not_ready")
        processor = app.state.video_worker.processor
        cuts = {}
        original_process = processor.process
        original_phase = processor.store.phase

        def measured(job):
            cuts["started"] = time.monotonic()
            return original_process(job)

        def phase(job_id, name, *args, **kwargs):
            if name == "encoding" and "analysis_seconds" not in cuts:
                cuts["analysis_seconds"] = time.monotonic() - cuts["started"]
            return original_phase(job_id, name, *args, **kwargs)

        processor.process = measured
        processor.store.phase = phase
        owner = Principal("benchmark")
        with a.video.open("rb") as stream:
            job = await app.state.video_job_service.create(
                owner,
                UploadFile(
                    stream,
                    filename="authorized.mp4",
                    headers=Headers({"content-type": "video/mp4"}),
                ),
                **({"progressive": True} if a.child == "progressive" else {}),
            )
        start = time.monotonic()
        first = None
        enrich_id = None
        while True:
            await asyncio.sleep(0.05)
            j = app.state.video_jobs.get(job.job_id, owner.key_id)
            if a.child == "progressive":
                state = app.state.progressive_store.snapshot(job.job_id, owner.key_id)
                if first is None and state["available_until_us"] >= 5_000_000:
                    first = time.monotonic() - start
                done = (
                    state["analysis_state"] in ("complete", "partial_failed")
                    and state["enrichment"]["status"]
                    in ("complete", "partial", "failed", "not_applicable")
                    and j.status.value in ("completed", "failed", "cancelled")
                )
            else:
                if j.status == VideoJobStatus.COMPLETED and enrich_id is None:
                    try:
                        enrich_id = app.state.enrichment_job_service.create(
                            "video", job.job_id, owner.key_id
                        ).enrichment_job_id
                    except Exception as e:
                        if getattr(e, "code", None) == "no_eligible_vehicles":
                            enrich_id = ""
                        else:
                            raise
                done = (
                    j.status.value in ("failed", "cancelled")
                    or j.status == VideoJobStatus.COMPLETED
                    and (
                        enrich_id == ""
                        or enrich_id
                        and app.state.enrichment_jobs.get(enrich_id, owner.key_id).status.value
                        in ("completed", "failed", "cancelled")
                    )
                )
            if done or time.monotonic() - start > a.timeout + 300:
                break
        result = dict(
            source_sha256=fingerprint,
            analysis_seconds=cuts.get("analysis_seconds"),
            arm=a.child,
            elapsed_seconds=time.monotonic() - start,
            outcome=j.status.value,
            frames=j.processed_frames,
            error=j.error_code,
            first_five_seconds_commit=first,
        )
        if a.child == "progressive":
            result["phase_totals_ms"] = getattr(
                app.state.video_worker.processor, "progressive_metrics", {}
            )
            result.update(
                analysis_state=state["analysis_state"],
                enrichment_status=state["enrichment"]["status"],
                published=state["frames_published"],
            )
        (a.runtime / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")


def main(a):
    a.video = a.video.resolve()
    a.runtime = a.runtime.resolve()
    a.env = a.env.resolve()
    if a.code:
        a.code = a.code.resolve()
    a.runtime.mkdir(parents=True, exist_ok=True)
    if a.child:
        return asyncio.run(child(a))
    import psutil

    root = Path(__file__).resolve().parents[2]
    a.runtime.mkdir(parents=True, exist_ok=True)
    baseline = a.runtime / "baseline"
    if not baseline.exists():
        blob = subprocess.check_output(["git", "archive", "--format=zip", REFERENCE], cwd=root)
        baseline.mkdir()
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            for name in z.namelist():
                if not (baseline / name).resolve().is_relative_to(baseline.resolve()):
                    raise RuntimeError("unsafe_archive")
            z.extractall(baseline)
    digest = hashlib.file_digest(a.video.open("rb"), "sha256").hexdigest()
    candidate = code_hash(root)
    report = dict(
        reference=REFERENCE,
        candidate_source_sha256=candidate,
        corpus_sha256=digest,
        timeout_seconds=a.timeout,
        pairs=[],
        rss_scope="backend process tree including OCR/encoder; active gateway and player measured separately",
        acceptance_note="Cost and policy evidence only; human and browser gates require separate reports.",
    )
    for pair, order in enumerate(
        (["legacy", "progressive"], ["progressive", "legacy"], ["legacy", "progressive"]), 1
    ):
        trials = []
        for arm in order:
            if code_hash(root) != candidate:
                raise RuntimeError("candidate_changed_during_evaluation")
            folder = a.runtime / f"pair-{pair}-{arm}"
            folder.mkdir(exist_ok=True)
            result = folder / "result.json"
            if result.exists():
                trial = json.loads(result.read_text(encoding="utf-8"))
            else:
                command = [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--child",
                    arm,
                    "--video",
                    str(a.video.resolve()),
                    "--runtime",
                    str(folder.resolve()),
                    "--env",
                    str(a.env.resolve()),
                    "--timeout",
                    str(a.timeout),
                    "--code",
                    str((baseline if arm == "legacy" else root).resolve()),
                ]
                with (folder / "private.log").open("wb") as log:
                    process = subprocess.Popen(
                        command,
                        stdout=log,
                        stderr=log,
                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                    )
                    peak = 0
                    last_print = time.monotonic()
                    while process.poll() is None:
                        try:
                            parent = psutil.Process(process.pid)
                            peak = max(
                                peak,
                                sum(
                                    p.memory_info().rss
                                    for p in [parent, *parent.children(recursive=True)]
                                    if p.is_running()
                                ),
                            )
                        except psutil.Error:
                            pass
                        if time.monotonic() - last_print >= 30:
                            print(
                                f"pair={pair} arm={arm} running peak_mb={peak / 1024**2:.1f}",
                                flush=True,
                            )
                            last_print = time.monotonic()
                        time.sleep(0.05)
                trial = (
                    json.loads(result.read_text(encoding="utf-8"))
                    if result.exists()
                    else dict(arm=arm, outcome="harness_failed", exit_code=process.returncode)
                )
                trial["peak_process_tree_rss_bytes"] = peak
                result.write_text(json.dumps(trial, indent=2), encoding="utf-8")
            trials.append(trial)
            print(json.dumps(dict(pair=pair, **trial)), flush=True)
        by = {t["arm"]: t for t in trials}
        legacy, new = by["legacy"], by["progressive"]
        valid = all(t.get("outcome") == "completed" for t in trials)
        report["pairs"].append(
            dict(
                pair=pair,
                order=order,
                trials=trials,
                quality=compare_quality(a.runtime, pair) if valid else None,
                comparable=valid,
                analysis_time_ratio=(new.get("analysis_seconds") or 0)
                / max(legacy.get("analysis_seconds") or 1, 0.001)
                if valid
                else None,
                time_ratio=new.get("elapsed_seconds", 0)
                / max(legacy.get("elapsed_seconds", 1), 0.001)
                if valid
                else None,
                rss_ratio=new.get("peak_process_tree_rss_bytes", 0)
                / max(legacy.get("peak_process_tree_rss_bytes", 1), 1)
                if valid
                else None,
            )
        )
        (a.runtime / "aggregate.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Isolated paired runs complete.", flush=True)


if __name__ == "__main__":
    main(arguments())
