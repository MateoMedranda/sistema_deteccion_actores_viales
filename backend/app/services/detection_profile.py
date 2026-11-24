"""Bounded nested accounting of timings already reported by Ultralytics.

These are children of the detection stage, never additional pipeline stages.
Missing or inconsistent telemetry is reported rather than guessed/rescaled.
"""
from __future__ import annotations

from collections.abc import Mapping
from math import isfinite
from numbers import Real

PHASES = {"preparation": "preprocess", "inference": "inference", "postprocessing": "postprocess"}


class DetectionBreakdown:
    def __init__(self):
        self.recorded = self.native = self.missing = self.invalid = self.exceeds_wall = 0
        self.phases = {key: dict(calls=0, total_ms=0.0, max_ms=0.0) for key in PHASES}
        self.predict_wall = dict(calls=0, total_ms=0.0, max_ms=0.0)
        self.transfer = dict(calls=0, total_ms=0.0, max_ms=0.0)

    @staticmethod
    def add(row, value):
        row["calls"] += 1
        row["total_ms"] += value
        row["max_ms"] = max(row["max_ms"], value)

    def record(self, speed, predict_ms, transfer_ms):
        self.recorded += 1
        self.add(self.predict_wall, max(0, predict_ms))
        self.add(self.transfer, max(0, transfer_ms))
        if not isinstance(speed, Mapping) or any(key not in speed for key in PHASES.values()):
            self.missing += 1
            return
        values = {name: speed[key] for name, key in PHASES.items()}
        if any(not isinstance(value, Real) or isinstance(value, bool) for value in values.values()):
            self.invalid += 1
            return
        try:
            values = {name: float(value) for name, value in values.items()}
        except (OverflowError, ValueError):
            self.invalid += 1
            return
        if (any(not isfinite(value) or value < 0 for value in values.values())
                or not isfinite(sum(values.values()) + sum(row["total_ms"] for row in self.phases.values()))):
            self.invalid += 1
            return
        self.native += 1
        if sum(values.values()) > predict_ms + max(.1, predict_ms * .01):
            self.exceeds_wall += 1
        for key, value in values.items():
            self.add(self.phases[key], float(value))

    def snapshot(self, parent_ms, parent_calls, frames):
        def stats(row):
            percent=(row["total_ms"] / parent_ms * 100) if parent_ms and row["calls"] else None
            if percent is not None and not isfinite(percent):percent=None
            return dict(calls=row["calls"], total_ms=round(row["total_ms"], 3),
                mean_call_ms=round(row["total_ms"] / row["calls"], 3) if row["calls"] else None,
                max_call_ms=round(row["max_ms"], 3) if row["calls"] else None,
                ms_per_processed_frame=round(row["total_ms"] / frames, 3) if frames and row["calls"] else None,
                detection_percent=round(percent, 3) if percent is not None else None)
        native_total = sum(row["total_ms"] for row in self.phases.values())
        remainder = parent_ms - native_total - self.transfer["total_ms"]
        return dict(source="ultralytics.Results.speed", unit="ms", included_in="stages.detection",
            recorded_calls=self.recorded, native_timing_calls=self.native,
            missing_native_timing_calls=self.missing, invalid_native_timing_calls=self.invalid,
            unrecorded_detection_calls=max(0, parent_calls - self.recorded),
            native_exceeds_wall_calls=self.exceeds_wall,
            parent_detection_ms=round(parent_ms, 3), native_total_ms=round(native_total, 3),
            phases={key: stats(row) for key, row in self.phases.items()},
            predict_wall=stats(self.predict_wall), boxes_transfer=stats(self.transfer),
            unattributed_detection_ms=round(max(0, remainder), 3),
            overreported_ms=round(max(0, -remainder), 3),
            notes="Nested timings: do not add to pipeline totals. Native phases cover successful "
            "predict calls with complete finite telemetry. Unattributed time includes setup, warmup, "
            "callbacks, orchestration and instrumentation; when coverage is incomplete it also "
            "contains unknown model work. No rescaling or invented phase timings.")


def render_detection_breakdown(data):
    detail = data.get("detection_breakdown")
    if detail is None:
        return ["", "Este informe anterior no contiene desglose interno; procesa un analisis nuevo."]
    def value(number):
        return "n/d" if number is None else f"{number:.2f}"
    parent_calls = data["stages"]["detection"]["calls"]
    rows = ["", "Desglose interno de deteccion (ya incluido arriba; NO sumar otra vez)",
        f"Llamadas con fases nativas: {detail['native_timing_calls']} / {parent_calls}. "
        f"Sin telemetria: {detail['missing_native_timing_calls']}; invalidas: {detail['invalid_native_timing_calls']}; "
        f"sin desglose registrado: {detail['unrecorded_detection_calls']}.",
        f"{'Fase':43} {'Total ms':>12} {'ms/llamada':>12} {'ms/cuadro':>11} {'% deteccion':>12}"]
    for key, label in (("preparation", "Preparacion de entrada"), ("inference", "Inferencia de la red"),
                       ("postprocessing", "Posprocesamiento"), ("boxes_transfer", "Transferencia de cajas a CPU/NumPy")):
        row = detail[key] if key == "boxes_transfer" else detail["phases"][key]
        rows.append(f"{label:43} {row['total_ms']:12.2f} {value(row['mean_call_ms']):>12} "
                    f"{value(row['ms_per_processed_frame']):>11} {value(row['detection_percent']):>12}")
    rows.append(f"No atribuido a fases: {detail['unattributed_detection_ms']:.2f} ms (incluye trabajo desconocido si falta telemetria).")
    if detail["native_exceeds_wall_calls"] or detail["overreported_ms"] > .1:
        rows.append(f"Discrepancia de relojes: {detail['native_exceeds_wall_calls']} llamadas; "
                    f"exceso agregado {detail['overreported_ms']:.3f} ms. No se han ajustado los tiempos.")
    return rows
