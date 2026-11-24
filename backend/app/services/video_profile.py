"""Bounded, local wall-clock profiling of one progressive processing job.

This measures the existing work, not model accuracy or browser playback FPS.
No frames, plates, source paths, credentials or per-vehicle data are retained.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
import json
import os
from pathlib import Path
import platform
import sys
from time import perf_counter


ANALYSIS_STAGES = (
    "setup", "decode", "resource_wait", "detection", "tracking",
    "detection_tracking_combined", "presentation", "evidence", "annotation",
    "video_write", "publication", "controls", "frame_logging", "profile_reporting",
)
STAGES = (*ANALYSIS_STAGES, "final_encode", "finalization", "cleanup")
LABELS = {
    "setup": "Preparacion", "decode": "Decodificacion",
    "resource_wait": "Espera de recurso compartido", "detection": "Deteccion YOLO",
    "tracking": "Seguimiento y conversion de cajas",
    "detection_tracking_combined": "Deteccion + seguimiento sin separar",
    "presentation": "Preparacion y suavizado visual", "evidence": "Seleccion y guardado de recortes",
    "annotation": "Dibujo de cajas en backend", "video_write": "Escritura del video anotado",
    "publication": "Publicacion en base de datos", "controls": "Controles y consultas de estado",
    "frame_logging": "Log y consulta de memoria por cuadro",
    "profile_reporting": "Guardado periodico de este informe",
    "final_encode": "Conversion final H.264", "finalization": "Cierre de estados",
    "cleanup": "Liberacion y limpieza",
}


def environment(detector):
    packages = {}
    for name in ("torch", "ultralytics", "av", "opencv-python-headless"):
        module = sys.modules.get(name)
        try:
            packages[name] = getattr(module, "__version__", None) or version(name)
        except PackageNotFoundError:
            packages[name] = None
    return {
        "python": platform.python_version(), "system": platform.system(),
        "logical_cpus": os.cpu_count(), "packages": packages,
        "device": getattr(detector, "_device", "unspecified"),
        "model": Path(getattr(detector, "model_name", "unspecified")).name,
        "confidence_threshold": getattr(detector, "_confidence_threshold", None),
    }


class VideoProfile:
    def __init__(self, job, detector, root: Path, clock=perf_counter):
        self.clock, self.started = clock, clock()
        self.job_id, self.root = job.job_id, Path(root)
        self.created_at = datetime.now(UTC).isoformat()
        self.context = environment(detector)
        self.source = {key: getattr(job.metadata, key) for key in (
            "width", "height", "fps", "duration_seconds", "total_frames")}
        self.stages = {key: dict(calls=0, total_ms=0.0, max_ms=0.0) for key in STAGES}
        self.frames = self.confirmed_frames = self.confirmed_us = 0
        self.analysis_ms = None
        self.analysis_complete = False
        self.first_publication_ms = self.initial_buffer_ms = None
        self.last_report = self.started
        self.outcome, self.error_code = "processing", None

    @contextmanager
    def measure(self, stage):
        before = self.clock()
        try:
            yield
        finally:
            elapsed = max(0.0, (self.clock() - before) * 1000)
            row = self.stages[stage]
            row["calls"] += 1
            row["total_ms"] += elapsed
            row["max_ms"] = max(row["max_ms"], elapsed)

    def confirmed(self, frames, until_us, buffer_seconds):
        self.confirmed_frames, self.confirmed_us = frames, until_us
        elapsed = (self.clock() - self.started) * 1000
        if self.first_publication_ms is None:
            self.first_publication_ms = elapsed
        if self.initial_buffer_ms is None and until_us >= buffer_seconds * 1_000_000:
            self.initial_buffer_ms = elapsed

    def end_analysis(self, complete=False):
        if self.analysis_ms is None:
            self.analysis_ms = max(0.0, (self.clock() - self.started) * 1000)
            self.analysis_complete = complete

    def snapshot(self):
        elapsed = max(0.0, (self.clock() - self.started) * 1000)
        analysis = self.analysis_ms if self.analysis_ms is not None else elapsed
        accounted = sum(self.stages[key]["total_ms"] for key in ANALYSIS_STAGES)
        stages = {}
        for key, row in self.stages.items():
            total, calls = row["total_ms"], row["calls"]
            stages[key] = {
                "calls": calls, "total_ms": round(total, 3),
                "mean_call_ms": round(total / calls, 3) if calls else 0,
                "ms_per_processed_frame": round(total / self.frames, 3) if self.frames else None,
                "max_call_ms": round(row["max_ms"], 3),
                "analysis_percent": round(total / analysis * 100, 3)
                if key in ANALYSIS_STAGES and analysis > 0 else None,
            }
        fps = self.frames * 1000 / analysis if analysis > 0 else 0
        confirmed_seconds = self.confirmed_us / 1_000_000
        return {
            "schema_version": 1, "job_id": self.job_id, "created_at": self.created_at,
            "updated_at": datetime.now(UTC).isoformat(), "outcome": self.outcome,
            "error_code": self.error_code, "environment": self.context, "source": self.source,
            "processed_frames": self.frames, "confirmed_frames": self.confirmed_frames,
            "confirmed_video_seconds": round(confirmed_seconds, 6),
            "analysis_complete": self.analysis_complete, "analysis_wall_ms": round(analysis, 3),
            "total_wall_ms": round(elapsed, 3), "analysis_fps": round(fps, 3),
            "confirmed_video_seconds_per_wall_second": round(confirmed_seconds * 1000 / analysis, 4)
            if analysis > 0 else 0,
            "first_publication_ms": self.first_publication_ms,
            "initial_buffer_available_ms": self.initial_buffer_ms,
            "other_analysis_ms": round(max(0, analysis - accounted), 3),
            "stages": stages,
            "scope": "Worker wall time only; excludes upload, queue, model loading and browser. "
            "Detection includes preprocess/predict/postprocess and CPU transfer. "
            "Stage totals are exclusive; final encoding and cleanup are outside analysis. "
            "Timing includes contention and OS scheduling, not CPU utilization. "
            "No per-frame samples or recognition data are stored.",
        }

    def save(self, logger):
        """Atomic bounded summary; a reporting failure must never fail analysis."""
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            path = self.root / (self.job_id + ".json")
            temporary = path.with_suffix(".json.tmp")
            temporary.write_text(json.dumps(self.snapshot(), indent=2, allow_nan=False), encoding="utf-8")
            temporary.replace(path)
            return True
        except (OSError, ValueError, TypeError):
            logger.warning("video_profile_write_failed", extra={"job_id": self.job_id})
            return False

    def checkpoint(self, logger):
        if self.clock() - self.last_report >= 5:
            self.last_report = self.clock()
            with self.measure("profile_reporting"):
                self.save(logger)


def render_report(data):
    def number(value):
        return "n/d" if value is None else f"{value:.2f}"
    lines = [
        f"Trabajo: {data['job_id']} | Estado: {data['outcome']} | Error: {data['error_code'] or '-'}",
        f"Modelo: {data['environment']['model']} | Dispositivo: {data['environment']['device']}",
        f"Fuente: {data['source']['width']}x{data['source']['height']} | FPS nominales: {data['source']['fps']}",
        f"Cuadros procesados/confirmados: {data['processed_frames']}/{data['confirmed_frames']}",
        f"Analisis completo: {data['analysis_complete']} | Analisis: {data['analysis_wall_ms']/1000:.2f} s | Total: {data['total_wall_ms']/1000:.2f} s",
        f"FPS efectivos del analisis: {data['analysis_fps']:.2f}",
        f"Segundos de video confirmado por segundo de trabajo: {data['confirmed_video_seconds_per_wall_second']:.3f} (>=1 sostiene el ritmo medio)",
        f"Primera publicacion: {number(data['first_publication_ms'])} ms | Buffer inicial disponible: {number(data['initial_buffer_available_ms'])} ms",
        "", f"{'Etapa':43} {'Total ms':>12} {'ms/cuadro':>11} {'% analisis':>11} {'Llamadas':>9}",
    ]
    for key, row in data["stages"].items():
        lines.append(f"{LABELS.get(key,key):43} {row['total_ms']:12.2f} {number(row['ms_per_processed_frame']):>11} {number(row['analysis_percent']):>11} {row['calls']:9}")
    lines.extend([f"Otros tiempos no desglosados: {data['other_analysis_ms']:.2f} ms", "", data["scope"],
                  "El buffer disponible se mide en backend; no es el primer cuadro visto en navegador.",
                  "Comparar una ejecucion sin seleccionar vehiculos con otra con consultas permite observar la espera compartida."])
    return "\n".join(lines)
