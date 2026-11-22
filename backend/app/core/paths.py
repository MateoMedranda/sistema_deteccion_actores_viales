"""Stable locations for the backend and the shared Speckit workspace."""
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent

def backend_path(value: Path) -> Path:
    """Keep shared project artifacts at the workspace root; store runtime under backend."""
    if value.is_absolute():
        return value
    base = PROJECT_ROOT if value.parts and value.parts[0] in {"specs", "frontend", ".specify", "metricas"} else BACKEND_ROOT
    return (base / value).resolve()
