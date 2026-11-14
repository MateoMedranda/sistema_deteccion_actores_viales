---

description: "Tareas de implementación para procesamiento vial por video"
---

# Tasks: Procesamiento vial por video

**Input**: Artefactos de diseño en `/specs/002-procesamiento-video-vial/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml y
quickstart.md.

**Tests**: Obligatorios. La especificación y la constitución exigen pruebas unitarias, de
integración, contrato, E2E y rendimiento proporcionales al riesgo.

**Organization**: Las tareas se agrupan por historia de usuario para permitir incrementos
independientes. Los elementos compartidos de cola, seguridad y persistencia se completan antes de
las historias.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Puede ejecutarse en paralelo porque modifica archivos distintos y no depende de una
  tarea incompleta de la misma fase.
- **[USn]**: Historia de usuario a la que pertenece la tarea.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Preparar dependencias reproducibles, configuración no secreta y dobles de prueba para
video.

- [X] T001 Add `psutil` and document the required FFmpeg/ffprobe runtime dependency with reproducible version guidance in `pyproject.toml` and `README.md`
- [X] T002 [P] Add non-secret video-job settings for 100 MiB, 120 seconds, 1920×1080, 30 fps, 3600 frames, 300-second timeout, one worker, 60-minute result TTL, SQLite path and private video directory in `.env.example`
- [X] T003 [P] Extend ignored local-runtime patterns for the SQLite queue, staged videos, annotated MP4s and video benchmark output in `.gitignore`
- [X] T004 [P] Create deterministic MP4/H.264 fixture builders, fake ffprobe adapter, fake tracker and authorized principals in `tests/video_fixtures.py`
- [X] T005 [P] Create video-specific test packages and controlled E2E asset manifest under `tests/contract/`, `tests/integration/`, `tests/unit/`, `tests/performance/` and `tests/e2e/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implementar configuración, autenticación previa a multipart, entidades, persistencia
temporal y ciclo de vida compartidos.

**⚠️ CRITICAL**: No iniciar las historias de usuario hasta completar esta fase.

### Tests for Foundational Infrastructure

- [X] T006 [P] Add configuration tests for `MAX_VIDEO_UPLOAD_BYTES=104857600`, `MAX_VIDEO_DURATION_SECONDS=120`, `MAX_VIDEO_WIDTH=1920`, `MAX_VIDEO_HEIGHT=1080`, `MAX_VIDEO_FPS=30`, `MAX_VIDEO_FRAMES=3600`, `MAX_CONCURRENT_VIDEO_JOBS=1`, `VIDEO_JOB_TIMEOUT_SECONDS=300` and `VIDEO_RESULT_TTL_SECONDS=3600` in `tests/unit/test_video_config.py`
- [X] T007 [P] Add tests for legacy single-key and multi-key principals, constant-time comparison and no secret logging in `tests/unit/test_video_auth.py`
- [X] T008 [P] Add tests for `queued → processing → completed`, `queued → cancelled`, `queued → failed`, `processing → cancelled`, `processing → failed`, terminal immutability and restart recovery to `queued` in `tests/unit/test_video_job_store.py`

### Implementation for Foundational Infrastructure

- [X] T009 Extend typed settings with video limits, timeout, worker concurrency, SQLite/private paths, TTL and external FFmpeg executable configuration in `app/core/config.py`
- [X] T010 Extend API-key handling to return a `Principal(key_id)` while mapping the existing single `API_KEY` to a default principal in `app/api/dependencies.py`
- [X] T011 Add pre-upload API-key middleware that rejects `POST /api/v1/video-jobs` before multipart parsing or disk staging in `app/api/upload_auth.py` and register it in `app/main.py`
- [X] T012 Define `VideoJob`, `VideoJobStatus`, `VideoMetadata`, `FrameDetection`, `VideoResult`, `VideoArtifact` and the exact state-transition guard in `app/domain/models.py`
- [X] T013 Define typed public schemas for job acceptance, job status, safe errors, class summaries, temporary video and paginated detections in `app/domain/schemas.py`
- [X] T014 Define a typed ffprobe/FFmpeg adapter protocol that exposes verified container, codec, size, duration, dimensions, fps and total frames in `app/adapters/video_probe.py`
- [X] T015 Implement SQLite schema initialization, owner-filtered lookup, atomic dequeue/requeue, cleanup and pagination in `app/services/video_job_store.py`
- [X] T016 Implement random private paths and cleanup for staged input and temporary annotated output in `app/services/video_artifacts.py`
- [X] T017 Extend structured logging with `job_id`, `owner_key_id`, progress, per-frame timing, process memory and safe error code fields in `app/core/logging.py`
- [X] T018 Initialize the video store, artifact manager and idle worker lifecycle, and atomically requeue non-expired interrupted jobs on startup in `app/core/lifespan.py`

**Checkpoint**: La aplicación tiene configuración validada, una cola temporal recuperable y una
autenticación que se aplica antes de aceptar videos.

---

## Phase 3: User Story 1 - Enviar un video vial para análisis (Priority: P1) 🎯 MVP

**Goal**: Un usuario autorizado carga un MP4/H.264 válido y recibe un trabajo `queued` sin esperar
el análisis completo; entradas no válidas o no autorizadas no crean trabajo ni archivos.

**Independent Test**: Cargar un video controlado válido devuelve `202` con `job_id` y `queued` en
≤2 s; tipo, códec, duración, resolución, fps, cuadros, tamaño y credenciales inválidas se rechazan
antes de persistir un trabajo o un archivo.

### Tests for User Story 1

- [X] T019 [P] [US1] Add OpenAPI contract tests for `POST /v1/video-jobs`, its `202`, `401`, `413`, `415`, `422` and `503` responses in `tests/contract/test_video_jobs_contract.py`
- [X] T020 [P] [US1] Add unit tests for streamed size limits and verified MP4/H.264 metadata including `duration_seconds <= 120`, `width <= 1920`, `height <= 1080`, `fps <= 30` and `total_frames <= 3600` in `tests/unit/test_video_validation.py`
- [X] T021 [P] [US1] Add integration tests proving valid upload returns a unique queued job in ≤2 s and invalid/corrupt videos create neither job nor staged artifact in `tests/integration/test_video_job_routes.py`
- [X] T022 [P] [US1] Add integration tests proving unauthenticated upload is rejected before multipart staging and interrupted non-expired queued work is recovered after restart in `tests/integration/test_video_job_recovery.py`

### Implementation for User Story 1

- [X] T023 [US1] Implement streamed staging, FFmpeg/ffprobe verification and safe rejection for only MP4/H.264 videos within all configured limits in `app/services/video_validation.py`
- [X] T024 [US1] Implement the job-creation service that stages only validated video, persists a UUID job owned by `Principal.key_id` and enqueues it atomically in `app/services/video_job_service.py`
- [X] T025 [US1] Implement protected `POST /v1/video-jobs` with `202` response and public safe errors in `app/api/routes/video_jobs.py`
- [X] T026 [US1] Register the video-job router and its documented OpenAPI metadata without changing existing image routes in `app/main.py`
- [X] T027 [US1] Run the US1 contract, unit and integration tests from `tests/contract/test_video_jobs_contract.py`, `tests/unit/test_video_validation.py`, `tests/integration/test_video_job_routes.py` and `tests/integration/test_video_job_recovery.py`

**Checkpoint**: Un usuario autorizado puede crear un trabajo de video validado; el servicio no
acepta ni almacena contenido no autorizado o inválido.

---

## Phase 4: User Story 2 - Consultar y cancelar un trabajo de video (Priority: P2)

**Goal**: El usuario consulta avance y estado de sus trabajos, obtiene páginas de resultados al
terminar y puede cancelar trabajos no terminales sin dejar resultados expuestos.

**Independent Test**: Con trabajos controlados en estados `queued`, `processing`, `completed` y
`cancelled`, el usuario ve solo los propios, recibe páginas consistentes y puede cancelar antes de
un resultado final.

### Tests for User Story 2

- [X] T028 [P] [US2] Add OpenAPI contract tests for `GET`/`DELETE /v1/video-jobs/{jobId}` and paginated `GET /detections` in `tests/contract/test_video_jobs_contract.py`
- [X] T029 [P] [US2] Add unit tests for owner isolation, `page` from 1, `page_size` from 1 to 100, ordered `(frame_index, track_id)` results and terminal cancellation conflict in `tests/unit/test_video_job_store.py`
- [X] T030 [P] [US2] Add integration tests for progress, other-principal invisibility, queued/processing cancellation, terminal conflict, result-not-ready and expired jobs in `tests/integration/test_video_job_routes.py`
- [X] T031 [P] [US2] Add artifact-access tests for same-principal retrieval, invalid credentials, cancelled output absence and 60-minute TTL behavior in `tests/integration/test_video_artifact_access.py`

### Implementation for User Story 2

- [X] T032 [US2] Implement owner-filtered status lookup, public progress projection, ordered detection pagination and terminal-state conflict rules in `app/services/video_job_store.py`
- [X] T033 [US2] Implement cooperative cancellation request, cancellation cleanup and expiration cleanup in `app/services/video_job_service.py` and `app/services/video_artifacts.py`
- [X] T034 [US2] Implement protected status, cancellation and paginated-detection endpoints with `404`, `409` and `410` safe responses in `app/api/routes/video_jobs.py`
- [X] T035 [US2] Implement protected annotated-video retrieval using owner-scoped temporary artifacts in `app/api/routes/video_jobs.py`
- [X] T036 [US2] Run the US2 contract, unit and integration tests from `tests/contract/test_video_jobs_contract.py`, `tests/unit/test_video_job_store.py`, `tests/integration/test_video_job_routes.py` and `tests/integration/test_video_artifact_access.py`

**Checkpoint**: El usuario puede seguir y cancelar de forma segura sus propios trabajos sin exponer
progreso, resultados o artefactos de otra credencial.

---

## Phase 5: User Story 3 - Revisar actores rastreados en un video terminado (Priority: P3)

**Goal**: Un trabajo terminado entrega detecciones por fotograma con `track_id` ByteTrack,
resumen por clase y un MP4 anotado temporal.

**Independent Test**: Procesar un video vial controlado con un detector/rastreador determinista
mantiene el `track_id` de un actor entre fotogramas consecutivos, genera un resumen coherente y
produce una salida anotada recuperable.

### Tests for User Story 3

- [X] T037 [P] [US3] Add unit tests for resetting ByteTrack between jobs and preserving positive `track_id` values for consecutive visible frames in `tests/unit/test_video_processing.py`
- [X] T038 [P] [US3] Add unit tests for frame-bounds normalization, class summaries, MP4 annotation output and no partial publication after timeout/cancellation in `tests/unit/test_video_processing.py`
- [X] T039 [P] [US3] Add integration E2E test for a controlled video with stable track IDs, paginated detections, coherent summary and retrievable annotated MP4 in `tests/integration/test_video_job_routes.py`
- [X] T040 [P] [US3] Add contract assertions for completed `VideoJobResponse`, `FrameDetection`, `DetectionPage` and temporary video schemas in `tests/contract/test_video_jobs_contract.py`

### Implementation for User Story 3

- [X] T041 [US3] Implement a shared YOLOv10s ByteTrack adapter that resets per job, reuses the loaded model and maps frame outputs to normalized detections in `app/adapters/yolov10_tracker.py`
- [X] T042 [US3] Implement frame decoding, timeout/cancellation checkpoints, per-frame inference/annotation, ByteTrack persistence, SQLite detections, class summaries and FFmpeg MP4 output in `app/services/video_processing.py`
- [X] T043 [US3] Implement the bounded worker loop that atomically dequeues jobs, processes one job with the configured timeout, records failure/cancellation and never publishes partial output in `app/services/video_worker.py`
- [X] T044 [US3] Integrate the worker with shared model state, artifacts and job-store lifecycle in `app/core/lifespan.py`
- [X] T045 [US3] Expose completed summaries, paginated detections and temporary annotated-video URLs from the public job projections in `app/api/routes/video_jobs.py`
- [X] T046 [US3] Run the US3 unit, contract and integration tests from `tests/unit/test_video_processing.py`, `tests/contract/test_video_jobs_contract.py` and `tests/integration/test_video_job_routes.py`

**Checkpoint**: Un usuario puede recuperar datos rastreados y un video anotado temporal de su
trabajo terminado, sin mezclar resultados ni reinicializar el modelo por fotograma.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verificar seguridad, observabilidad, rendimiento, regresión de imagen y evidencia de
la constitución.

- [X] T047 [P] Add FFmpeg/ffprobe availability and version checks to startup readiness without exposing executable paths in `app/core/lifespan.py` and `app/api/routes/health.py`
- [X] T048 [P] Add structured job/frame metrics for upload, validation, inference, annotation, output, memory, errors, model version, ByteTrack, FFmpeg and non-secret configuration in `app/core/logging.py` and `tests/unit/test_video_worker.py`
- [ ] T049 [P] Add a 20-video reference benchmark that persists non-secret p95, hardware, model, ByteTrack, FFmpeg, memory, error and per-frame timing evidence in `tests/performance/test_video_reference_benchmark.py`
- [X] T050 [P] Add controlled E2E regression coverage for the existing image flow plus the new video flow in `tests/e2e/test_image_and_video_regression.py`
- [X] T051 Perform security review for pre-upload authorization, owner isolation, SQLite/file permissions, TTL cleanup, safe error bodies and no sensitive logging in `specs/002-procesamiento-video-vial/security-review.md`
- [X] T052 Update video settings, FFmpeg installation requirement, API examples, artifact retention, supported scope and run instructions in `README.md` and `.env.example`
- [ ] T053 Run the complete suite, execute every scenario in `specs/002-procesamiento-video-vial/quickstart.md`, record coverage and benchmark evidence in `specs/002-procesamiento-video-vial/quickstart.md`
- [X] T054 Review FR-001 through FR-014 and SC-001 through SC-006 against code and evidence, then record final traceability in `specs/002-procesamiento-video-vial/coverage.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sin dependencias; inicia de inmediato.
- **Foundational (Phase 2)**: Depende de Setup y bloquea todas las historias.
- **US1 (Phase 3)**: Depende de Foundational; entrega la carga segura y la cola persistente.
- **US2 (Phase 4)**: Depende de US1 porque consulta y cancela trabajos creados por esa historia.
- **US3 (Phase 5)**: Depende de US1 y US2 porque procesa, publica y recupera trabajos y
  artefactos ya aislados.
- **Polish (Phase 6)**: Depende de las tres historias.

### User Story Dependencies

- **US1 (P1)**: MVP independiente después de la infraestructura.
- **US2 (P2)**: Requiere trabajos de US1, pero sus pruebas usan estados controlados y no dependen
  de una inferencia real.
- **US3 (P3)**: Requiere el ciclo de trabajo y artefacto de US1/US2 para publicar procesamiento
  real de video.

### Parallel Opportunities

- T002-T005 pueden ejecutarse en paralelo.
- T006-T008 y T010-T014 pueden avanzar en paralelo tras acordar el contrato de configuración.
- Las pruebas T019-T022, T028-T031 y T037-T040 pueden ejecutarse en paralelo dentro de su historia.
- T047-T052 afectan archivos distintos en gran parte y pueden avanzar en paralelo al final.

## Parallel Example: User Story 1

```text
Task: "Add OpenAPI contract tests in tests/contract/test_video_jobs_contract.py"
Task: "Add video validation tests in tests/unit/test_video_validation.py"
Task: "Add upload and recovery integration tests in tests/integration/test_video_job_routes.py"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Completar Setup y Foundational.
2. Completar T019-T027.
3. Validar una carga MP4/H.264 autorizada, rechazos seguros y recuperación de cola.
4. Demostrar la creación asíncrona de trabajos antes de procesar video real.

### Incremental Delivery

1. Entregar US1: carga, validación, autenticación y encolado seguro.
2. Entregar US2: consulta, paginación, cancelación y acceso temporal aislado.
3. Entregar US3: ByteTrack, procesamiento por fotogramas, resumen y video anotado.
4. Completar evidencia de rendimiento, seguridad, E2E y auditoría.

## Notes

- Cada tarea contiene una ruta de archivo y un identificador secuencial.
- Las pruebas se escriben antes de su implementación asociada y deben fallar inicialmente.
- No se implementan frontend, cámara, conteo por línea, OCR, placas ni historial permanente.
