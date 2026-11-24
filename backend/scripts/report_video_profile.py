"""Read existing summaries; never starts inference or a benchmark."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from app.services.video_profile import render_report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Mostrar mediciones de un analisis de video existente.")
    select = parser.add_mutually_exclusive_group(required=True)
    select.add_argument("--latest", action="store_true", help="Ultimo informe actualizado")
    select.add_argument("--job", help="ID exacto de trabajo")
    parser.add_argument("--directory", type=Path, default=BACKEND / ".runtime" / "video-profiles")
    parser.add_argument("--json", action="store_true", help="Mostrar JSON completo para compartir")
    args = parser.parse_args(argv)
    if args.job and (Path(args.job).name != args.job or "/" in args.job or "\\" in args.job):
        parser.error("El ID debe ser un nombre de trabajo, no una ruta.")
    candidates = list(args.directory.glob("*.json")) if args.latest else [args.directory / (args.job + ".json")]
    if not candidates:
        parser.exit(1, "No hay informes. Reinicia la API actualizada y procesa un video; se guarda un avance cada cinco segundos y el resumen al terminar.\n")
    path = max(candidates, key=lambda p: p.stat().st_mtime_ns)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        parser.exit(1, f"No se pudo leer el informe ({type(exc).__name__}).\n")
    print(json.dumps(data, indent=2) if args.json else render_report(data))
    if not args.json:
        print(f"\nArchivo JSON para compartir: {path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
