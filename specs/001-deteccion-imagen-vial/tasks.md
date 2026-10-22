---

description: "Tareas de implementación para detección vial en una imagen"
---

# Tasks: Detección vial en imagen

**Input**: Artefactos de diseño en `/specs/001-deteccion-imagen-vial/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml,
quickstart.md

**Tests**: Obligatorios. La especificación exige pruebas para casos exitosos y de error, y la
constitución exige pruebas unitarias, de integración, contrato y rendimiento proporcional al riesgo.

**Organization**: Las tareas se agrupan por historia de usuario para permitir validar cada
incremento. Todas usan la estructura de una aplicación Python/FastAPI definida en `plan.md`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Puede ejecutarse en paralelo porque modifica archivos distintos y no depende de una tarea
  incompleta de la misma fase.
- **[USn]**: Relaciona la tarea con la historia de usuario correspondiente.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Crear la estructura reproducible del proyecto y su entorno de desarrollo.

- [X] T001 Create package and test directories with `__init__.py` files under `app/`, `app/api/routes/`, `app/core/`, `app/domain/`, `app/services/`, `app/adapters/`, `tests/unit/`, `tests/integration/`, `tests/contract/`, and `tests/performance/`
- [X] T002 Create Python 3.12 project metadata and pinned runtime/test dependencies in `pyproject.toml`
- [X] T003 [P] Create non-secret configuration template with model, API key, upload, pixel, TTL, concurrency, and device variables in `.env.example`
- [X] T004 [P] Create repository ignore rules for virtual environments, secret environment files, temporary artifacts, model weights, test cache, and coverage output in `.gitignore`
- [X] T005 [P] Create shared pytest fixtures for an authorized client, temporary artifact directory, sample images, and fake detector in `tests/conftest.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implementar infraestructura común que bloquea todas las historias de usuario.

**⚠️ CRITICAL**: No iniciar tareas de historias de usuario hasta completar esta fase.

- [X] T006 Implement typed environment settings and startup validation in `app/core/config.py`, including a required model-weights path, API key, confidence threshold between 0 and 1, positive limits, and a documented inference device
- [X] T007 [P] Implement JSON structured logging with request ID, source type, status, validation duration, inference duration, annotation duration, and total duration in `app/core/logging.py`
- [X] T008 [P] Define public error, health, bounding-box, image-metadata, and artifact response schemas in `app/domain/schemas.py`
- [X] T009 [P] Define internal analysis-request state, detection, and temporary-artifact entities in `app/domain/models.py`, including states `received`, `validated`, `processing`, `completed`, `rejected`, and `failed`
- [X] T010 [P] Define the detector protocol and a model-readiness interface in `app/adapters/detector_protocol.py`
- [X] T011 Implement API-key authentication with constant-time comparison and no credential logging in `app/api/dependencies.py`
- [X] T012 Implement shared safe error responses carrying `code`, `message`, and `request_id` in `app/api/error_handlers.py`
- [X] T013 Implement application lifespan startup/shutdown, load model once, inject shared state, and expose failure as not-ready in `app/core/lifespan.py`
- [X] T014 Implement liveness and readiness routes in `app/api/routes/health.py`
- [X] T015 Register routers, error handlers, lifespan, and OpenAPI metadata in `app/main.py`
- [X] T016 Add foundation integration tests for liveness, readiness-before-model, readiness-after-model, and missing/invalid API keys in `tests/integration/test_health_and_auth.py`

**Checkpoint**: La aplicación inicia de forma segura, el modelo tiene un ciclo de vida definido y las
rutas comunes están listas para implementar historias.

---

## Phase 3: User Story 1 - Analizar una imagen vial (Priority: P1) 🎯 MVP

**Goal**: El usuario autorizado envía una imagen válida y obtiene detecciones estructuradas más una
imagen anotada con cajas, clase y confianza.

**Independent Test**: Con el detector falso, enviar una imagen válida con detecciones y otra sin
detecciones; verificar la respuesta, recuperar la imagen anotada y comprobar que ambos resultados
quedan aislados por `request_id`.

### Tests for User Story 1

- [X] T017 [P] [US1] Add contract tests for successful `POST /v1/detections/images` responses, empty detections, bounding boxes, and annotated-image URL fields in `tests/contract/test_detection_contract.py`
- [X] T018 [P] [US1] Add unit tests for conversion of detector output to detections where confidence is between 0 and 1 and `bbox` contains `x_min`, `y_min`, `x_max`, and `y_max` in `tests/unit/test_detection_service.py`
- [X] T019 [P] [US1] Add unit tests that annotated output contains one box, class, and confidence label per detection in `tests/unit/test_annotation_service.py`
- [X] T020 [P] [US1] Add integration tests for successful image analysis, a no-detection result, unique request IDs, and artifact retrieval in `tests/integration/test_detection_routes.py`

### Implementation for User Story 1

- [X] T021 [P] [US1] Implement the YOLOv10s adapter that loads the approved weights and maps output to the detector protocol in `app/adapters/yolov10_detector.py`
- [X] T022 [P] [US1] Implement image annotation that draws bounding boxes, class names, and confidence values in `app/services/annotation_service.py`
- [X] T023 [P] [US1] Implement private temporary artifact creation and lookup with random identifiers, `image/jpeg` output, and a default 15-minute TTL in `app/services/temporary_artifacts.py`
- [X] T024 [US1] Implement orchestration of a validated image, detector call, metrics, annotated image, and response entities in `app/services/detection_service.py`
- [X] T025 [US1] Implement protected `POST /v1/detections/images` and `GET /v1/detections/{requestId}/annotated-image` routes in `app/api/routes/detections.py`
- [X] T026 [US1] Integrate detection routes, lifespan state, structured timing logs, and the success response contract in `app/main.py`
- [ ] T027 [US1] Run the US1 contract, unit, and integration tests from `tests/contract/test_detection_contract.py`, `tests/unit/test_detection_service.py`, `tests/unit/test_annotation_service.py`, and `tests/integration/test_detection_routes.py`

**Checkpoint**: Un usuario autorizado puede analizar una imagen válida y visualizar resultados
estructurados y anotados, incluso cuando no existan detecciones.

---

## Phase 4: User Story 2 - Recibir orientación ante una carga inválida (Priority: P2)

**Goal**: El usuario recibe rechazos seguros, claros y consistentes ante archivos no permitidos,
corruptos o excesivos.

**Independent Test**: Enviar archivo de texto, imagen corrupta, archivo mayor a 10 MiB y una imagen
cuya dimensión supere 16 megapíxeles; confirmar los códigos de contrato y que no quedan artefactos
temporales.

### Tests for User Story 2

- [X] T028 [P] [US2] Add unit tests for JPEG/PNG validation, content-signature/decode failure, 10 MiB limit, and 16-megapixel limit in `tests/unit/test_image_validation.py`
- [X] T029 [P] [US2] Add contract tests for `401`, `413`, `415`, and `422` error bodies without secrets, traces, or local paths in `tests/contract/test_error_responses.py`
- [X] T030 [P] [US2] Add integration tests for invalid media, corrupt images, oversized files, and oversized dimensions in `tests/integration/test_invalid_uploads.py`

### Implementation for User Story 2

- [X] T031 [US2] Implement streamed size enforcement, MIME allowlist (`image/jpeg`, `image/png`), safe decode, and 16-megapixel validation in `app/services/image_validation.py`
- [X] T032 [US2] Connect validation failures to the public error schema and ensure temporary upload cleanup in `app/services/detection_service.py`
- [X] T033 [US2] Map validation failures to `413`, `415`, and `422` contract responses in `app/api/routes/detections.py`
- [ ] T034 [US2] Run the US2 unit, contract, and integration tests from `tests/unit/test_image_validation.py`, `tests/contract/test_error_responses.py`, and `tests/integration/test_invalid_uploads.py`

**Checkpoint**: Las cargas inválidas se rechazan antes de inferencia con mensajes seguros y sin
generar resultados parciales ni archivos residuales.

---

## Phase 5: User Story 3 - Consumir resultados desde una interfaz cliente (Priority: P3)

**Goal**: Una interfaz cliente de prueba consume un contrato estable para mostrar detecciones y la
visualización anotada sin acceder a datos internos.

**Independent Test**: Una prueba cliente usa únicamente el contrato OpenAPI y la respuesta del
servicio para mostrar detecciones y recuperar la imagen anotada, sin usar rutas locales ni el modelo.

### Tests for User Story 3

- [X] T035 [P] [US3] Add contract tests that compare the generated OpenAPI schema and response models against `specs/001-deteccion-imagen-vial/contracts/openapi.yaml` in `tests/contract/test_openapi_contract.py`
- [X] T036 [P] [US3] Add integration tests for authorized artifact retrieval, incorrect credentials, unknown request IDs, and expired artifacts in `tests/integration/test_artifact_access.py`
- [X] T037 [P] [US3] Add a client-consumption test using 20 reference response fixtures without internal paths in `tests/integration/test_client_consumption.py`

### Implementation for User Story 3

- [X] T038 [US3] Implement artifact-expiry detection, deletion, and `410`/`404` behavior in `app/services/temporary_artifacts.py`
- [X] T039 [US3] Complete documented route metadata, response models, and security requirements so generated service documentation conforms to `specs/001-deteccion-imagen-vial/contracts/openapi.yaml` in `app/api/routes/detections.py`
- [X] T040 [US3] Add a documented sample consumer flow that uses only public fields and the temporary URL in `README.md`
- [ ] T041 [US3] Run the US3 contract and integration tests from `tests/contract/test_openapi_contract.py`, `tests/integration/test_artifact_access.py`, and `tests/integration/test_client_consumption.py`

**Checkpoint**: El contrato público permite a una interfaz de prueba representar las detecciones y
la imagen anotada sin conocer la implementación, los pesos ni las rutas privadas.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verificar rendimiento, seguridad, documentación y criterios de aceptación completos.

- [X] T042 [P] Add a 20-image reference benchmark that records hardware, model version, configuration, validation time, inference time, annotation time, total time, and 95th-percentile result in `tests/performance/test_reference_images.py`
- [X] T043 [P] Add cleanup lifecycle tests for rejected uploads, failed inference, expired artifacts, and orderly shutdown in `tests/unit/test_temporary_artifacts.py`
- [X] T044 [P] Document environment variables, secure deployment expectations, API-key handling, model provenance, and excluded scope in `README.md`
- [X] T045 Perform security review for API-key protection, non-secret logging, upload limits, private temporary storage, and artifact access using `specs/001-deteccion-imagen-vial/plan.md`
- [ ] T046 Run all automated tests, execute every validation scenario in `specs/001-deteccion-imagen-vial/quickstart.md`, and record the resulting evidence in `specs/001-deteccion-imagen-vial/quickstart.md`
- [ ] T047 Review FR-001 through FR-010 and SC-001 through SC-005 against the implementation and update completion evidence in `specs/001-deteccion-imagen-vial/spec.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; start immediately.
- **Foundational (Phase 2)**: Depends on Setup and blocks all user-story work.
- **US1 (Phase 3)**: Depends on Foundational; establishes the MVP and the public success flow.
- **US2 (Phase 4)**: Depends on Foundational and the shared detection route created by US1.
- **US3 (Phase 5)**: Depends on US1 because it consumes the successful response and artifact route.
- **Polish (Phase 6)**: Depends on all stories selected for this iteration.

### User Story Dependencies

- **US1 (P1)**: Independent after Foundational; it is the recommended MVP.
- **US2 (P2)**: Reuses the upload route from US1 but can be validated independently with invalid
  files after that route exists.
- **US3 (P3)**: Reuses the success and temporary-artifact contract from US1; it validates client
  compatibility rather than introducing a production UI.

### Parallel Opportunities

- T003, T004 and T005 can run in parallel after T001.
- T007, T008, T009 and T010 can run in parallel after T006 establishes configuration conventions.
- Within US1, T017-T020 and T021-T023 target different files and can be performed in parallel.
- Within US2, T028-T030 can run in parallel before T031.
- Within US3, T035-T037 can run in parallel before T038-T040.
- T042-T044 can run in parallel after all user stories are complete.

## Parallel Example: User Story 1

```text
Task: "Add contract tests in tests/contract/test_detection_contract.py"
Task: "Add annotation tests in tests/unit/test_annotation_service.py"
Task: "Implement YOLOv10s adapter in app/adapters/yolov10_detector.py"
Task: "Implement temporary artifacts in app/services/temporary_artifacts.py"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phases 1 and 2.
2. Complete T017 through T027.
3. Validate a valid image, an image with no detections, and the annotated-image retrieval flow.
4. Demonstrate the MVP before expanding to invalid-upload handling and client contract hardening.

### Incremental Delivery

1. Deliver US1: secure valid-image detection with annotated result.
2. Deliver US2: safe, user-oriented validation failures.
3. Deliver US3: contract compatibility and temporary artifact lifecycle.
4. Complete cross-cutting evidence and audit readiness.

## Notes

- All tasks use the required checkbox, sequential ID, optional parallel marker, story label, and
  exact file path.
- Tests must be written first within each user-story phase and should fail before the implementation
  task that satisfies them.
- No task implements video, camera, attributes, plates, persistent history, or a production web UI.

---

## Phase 7: Convergence

- [ ] T048 CRITICAL Register every validation rejection with request ID, source type, safe error code, validation duration, and rejected status in `app/api/routes/detections.py`; add focused coverage per Constitution II (partial)
- [ ] T049 CRITICAL Enforce allowed `.jpg`, `.jpeg`, and `.png` filename extensions in `app/services/image_validation.py` and add unit coverage, per Constitution II (partial)
- [X] T050 Align the annotated-image path parameter with `{requestId}` in `specs/001-deteccion-imagen-vial/contracts/openapi.yaml`, update `app/api/routes/detections.py`, and extend `tests/contract/test_openapi_contract.py` to compare the exact path, per US3/AC1 and contract (contradicts)
- [X] T051 Normalize every detection bounding box to the analyzed image bounds in `app/adapters/yolov10_detector.py` or `app/services/detection_service.py` and add unit coverage, per FR-004 and data-model.md (partial)
- [X] T052 Complete and use the `AnalysisRequest` lifecycle fields (`submitted_at`, processing time, public error code and state transitions) in `app/domain/models.py` and `app/services/detection_service.py`, per data-model.md (partial)
- [X] T053 Strengthen `tests/unit/test_annotation_service.py` so it verifies that each annotation emits the class name and confidence label, per T019 and Constitution IV (partial)
- [ ] T054 Capture and persist non-secret validation, inference, annotation, total-latency, model, device, hardware and p95 measurements in `tests/performance/test_reference_images.py`, per T042, SC-001 and Constitution V (partial)
