# Implementation Plan: Procesamiento vial por video

**Branch**: `002-procesamiento-video-vial` | **Date**: 2026-11-12 | **Spec**: [spec.md](spec.md)

## Summary

Ampliar el microservicio existente con trabajos temporales y asíncronos de video. Un usuario autorizado carga un MP4/H.264 dentro del perfil definido; recibe un identificador de trabajo y consulta su avance, resultado paginado, resumen por clase y video anotado. Un trabajador interno procesa fotogramas con el modelo ya cargado y ByteTrack, mientras una cola temporal persistente permite reanudar trabajos no vencidos después de reiniciar el servicio.

## Technical Context

**Language/Version**: Python 3.12.

**Primary Dependencies**: FastAPI, Uvicorn, Pydantic Settings, python-multipart, Ultralytics, OpenCV, pytest y httpx/TestClient; `sqlite3` de la biblioteca estándar para estado temporal; FFmpeg/ffprobe como dependencia de ejecución versionada para sondeo, lectura y codificación H.264; `psutil` para medición de memoria de proceso.

**Storage**: SQLite local temporal para trabajos, estados, páginas de detecciones y metadatos; directorio privado configurable para archivos de entrada y MP4 anotados. El archivo de entrada se elimina al terminar, fallar o cancelar; salida y metadatos expiran 60 minutos después de completar.

**Testing**: pytest con dobles de detector/rastreador y sondeo de video; pruebas unitarias de validación, transiciones, paginación y cancelación; integración HTTP y OpenAPI; prueba E2E con un video controlado; rendimiento con 20 videos de referencia, métricas por fotograma y memoria.

**Target Platform**: Desarrollo en Windows 11 con Python 3.12 y FFmpeg instalado; despliegue objetivo en Linux x86_64 con GPU NVIDIA/CUDA cuando exista. El dispositivo, versiones de modelo, FFmpeg y parámetros se registran en las mediciones.

**Project Type**: Microservicio web de una sola aplicación, sin frontend.

**Performance Goals**: Confirmación de carga en ≤2 s; ≥95% de 20 videos de referencia termina en ≤2× la duración del origen bajo hardware documentado; procesamiento, memoria y errores se miden por trabajo y por fotograma; el modelo se carga una vez por proceso.

**Constraints**: Solo MP4/H.264; ≤100 MiB, ≤120 s, ≤1920×1080, ≤30 fps y ≤3600 fotogramas; concurrencia y timeout configurables (inicialmente 1 trabajo y 300 s); detalle paginado; ByteTrack; estado recuperable hasta vencer; sin frontend, cámara, conteo por línea, OCR, placas ni historial.

**Scale/Scope**: Prototipo académico con una cola temporal persistente, un trabajador de video por defecto y 20 videos de referencia. La persistencia sirve exclusivamente para recuperación y TTL, no como historial de análisis.

## Constitution Check

*GATE: PASS before Phase 0 research. Re-checked after Phase 1 design: PASS, condicionado a las pruebas y métricas indicadas en este plan.*

| Principio | Diseño que asegura el cumplimiento |
|---|---|
| I. Arquitectura modular y contratos explícitos | Las rutas dependen del servicio de trabajos; la cola, el sondeo de video, el rastreador, la persistencia y los artefactos se abstraen detrás de interfaces tipadas. |
| II. Validación, errores y trazabilidad | Se autentica antes de leer multipart; se valida formato, códec, tamaño, duración, resolución y cuadros; los errores conservan el esquema público seguro y los logs son estructurados. |
| III. Seguridad y protección de datos | Cada trabajo queda ligado al identificador de la credencial; los nombres de archivo son aleatorios, la cola y artefactos son privados y se limpian por estado y TTL. |
| IV. Pruebas verificables y calidad del modelo | Se agregan unitarias, integración, contrato, rendimiento y E2E con video controlado; las métricas del modelo y ByteTrack se comparan con la línea base documentada. |
| V. Rendimiento y recursos | Un trabajador controlado reutiliza el modelo; timeout, concurrencia, latencias, tiempo por fotograma, memoria y errores se registran con evidencia reproducible. |

No se requiere una excepción: esta iteración incorpora la prueba de video controlado requerida por la constitución y reutiliza la prueba de imagen de la iteración 001 como regresión.

## Project Structure

### Documentation (this feature)

```text
specs/002-procesamiento-video-vial/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── openapi.yaml
├── checklists/
│   └── requirements.md
└── tasks.md                    # Created by $speckit-tasks
```

### Source Code (repository root)

```text
app/
├── adapters/
│   ├── detector_protocol.py         # Reused detector contract
│   ├── video_probe.py               # FFmpeg/ffprobe metadata and decode adapter
│   └── yolov10_tracker.py           # Shared model + ByteTrack adapter
├── api/
│   ├── dependencies.py              # Principal-aware API-key authentication
│   ├── upload_auth.py               # Authentication before multipart parsing
│   └── routes/
│       └── video_jobs.py            # Upload, status, cancel, page and artifact routes
├── core/
│   ├── config.py                    # Video limits, TTL, timeout, paths and concurrency
│   ├── lifespan.py                  # Shared model, store and worker lifecycle/recovery
│   └── logging.py                   # Job and frame metrics
├── domain/
│   ├── models.py                    # Video job, frame detection, artifact and status entities
│   └── schemas.py                   # Versioned public job/result response schemas
├── services/
│   ├── video_validation.py          # Streaming upload and video-profile validation
│   ├── video_job_store.py           # SQLite queue, ownership, transitions and pagination
│   ├── video_worker.py              # Persistent queue polling, cancellation and timeout control
│   ├── video_processing.py          # Frame pipeline, annotation, summary and persistence
│   └── video_artifacts.py           # Private input/output lifecycle and TTL cleanup
└── main.py                          # Router, pre-upload auth and worker registration

tests/
├── contract/
│   └── test_video_jobs_contract.py
├── integration/
│   ├── test_video_job_routes.py
│   ├── test_video_job_recovery.py
│   └── test_video_artifact_access.py
├── performance/
│   └── test_video_reference_benchmark.py
└── unit/
    ├── test_video_validation.py
    ├── test_video_job_store.py
    ├── test_video_processing.py
    └── test_video_worker.py
```

**Structure Decision**: Se mantiene una sola aplicación FastAPI. SQLite y el sistema de archivos son adaptadores temporales locales, no una nueva capa de historial. El trabajador se inicia y detiene con el ciclo de vida de la aplicación, de modo que comparte el modelo ya cargado sin acoplar rutas HTTP a Ultralytics, FFmpeg o el sistema de archivos.

## Complexity Tracking

No se requieren excepciones a la constitución.
