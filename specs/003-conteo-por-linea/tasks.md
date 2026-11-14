---

description: "Tareas implementables para conteo direccional de actores por línea"
---

# Tasks: Conteo de actores por línea

**Input**: Artefactos de diseño de `specs/003-conteo-por-linea/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/openapi.yaml` y `quickstart.md`.

**Tests**: Obligatorios por la constitución, los criterios de aceptación y el plan. Escribir cada prueba antes de la implementación que valida.

**Organization**: Las tareas se agrupan por historia de usuario para que cada incremento se pueda construir, probar y demostrar de forma independiente.

## Phase 1: Setup (Infraestructura compartida)

**Purpose**: Preparar los límites configurables y los puntos de integración de la nueva capacidad sin alterar el flujo de detección de video.

- [X] T001 [P] Añadir en `app/core/config.py` los límites configurables del trabajo de conteo (concurrencia, directorio temporal y retención) con valores seguros por defecto.
- [X] T002 [P] Preparar en `tests/video_fixtures.py` trayectorias y videos controlados reutilizables con `track_id`, clases, cruces, no-cruces y cruces simultáneos.
- [X] T003 Crear el esqueleto importable de `app/api/routes/count_jobs.py` y registrarlo en `app/api/routes/__init__.py` y `app/main.py` bajo el prefijo existente `/api`, sin crear rutas de frontend.

---

## Phase 2: Foundational (Prerrequisitos bloqueantes)

**Purpose**: Construir los contratos de dominio, almacenamiento temporal y ciclo de vida comunes que bloquean todas las historias.

**⚠️ CRITICAL**: No iniciar una historia de usuario antes de completar esta fase.

- [X] T004 Extender `app/domain/models.py` con `CountLine`, `CountJob`, `CountEvent`, `CountSummary`, `CountJobStatus` y transiciones `queued → processing → completed`; permitir únicamente `failed` o `cancelled` desde estados no terminales.
- [X] T005 Extender `app/domain/schemas.py` con DTOs tipados para punto normalizado, creación, estado/progreso, evento paginado, resumen y video temporal de conteo.
- [X] T006 Crear `app/services/count_job_store.py` con tablas SQLite, índices por propietario/expiración y operaciones atómicas para configuraciones, trabajos, eventos y agregados temporales.
- [X] T007 Crear `app/services/count_worker.py` para registrar, limitar y recuperar el trabajador asíncrono de conteo; reencolar trabajos `processing` no vencidos después de un reinicio.
- [X] T008 Integrar el almacén, limpieza por TTL y trabajador de conteo en `app/core/lifespan.py`, garantizando que un resultado no sobreviva al video fuente.
- [X] T009 Añadir en `app/api/error_handlers.py` códigos de error seguros y consistentes para línea inválida, video no terminado, conteo vencido y artefacto no disponible.

**Checkpoint**: Los modelos, almacenamiento, trabajador, limpieza y errores compartidos están disponibles para construir historias sin volver a ejecutar detección.

---

## Phase 3: User Story 1 - Configurar un conteo sobre un video terminado (Priority: P1) 🎯 MVP

**Goal**: Un usuario autorizado puede enviar dos puntos normalizados válidos para crear rápidamente un trabajo temporal de conteo sobre su propio video terminado.

**Independent Test**: Con un video `completed` y vigente del propietario, un `POST` válido responde `202` en menos de dos segundos; puntos inválidos, fuente vencida/no terminada y otra credencial se rechazan sin crear trabajo.

### Tests for User Story 1

- [X] T010 [P] [US1] Crear pruebas unitarias de rango, finitud, longitud cero y conversión de puntos en `tests/unit/test_line_counting.py`.
- [X] T011 [P] [US1] Crear prueba de contrato para `POST /api/v1/video-jobs/{videoJobId}/count-jobs` y sus respuestas `202`, `400`, `401`, `404`, `409` y `410` en `tests/contract/test_count_jobs_contract.py`.
- [X] T012 [P] [US1] Crear pruebas de integración de propietario, estado `completed`, vencimiento y confirmación menor a dos segundos en `tests/integration/test_count_job_routes.py`.

### Implementation for User Story 1

- [X] T013 [US1] Implementar en `app/services/line_counting.py` la validación de línea: "Coordenadas x/y finitas, normalizadas entre 0 y 1" y longitud que "Debe ser mayor que cero".
- [X] T014 [US1] Crear `app/services/count_job_service.py` para validar que el `source_video_job_id` pertenece al solicitante y está `completed` y no vencido antes de persistir un trabajo.
- [X] T015 [US1] Implementar en `app/services/count_job_store.py` la creación atómica de `CountLine` y `CountJob` con UUID público, estado `queued`, propietario y `expires_at` no posterior a la fuente.
- [X] T016 [US1] Añadir en `app/services/count_worker.py` el encolado no bloqueante del trabajo creado, respetando el límite de concurrencia configurado.
- [X] T017 [US1] Implementar en `app/api/routes/count_jobs.py` el endpoint de creación autenticado, respuesta `202` y errores que no revelen propiedad, rutas internas ni secretos.
- [X] T018 [US1] Registrar en `app/services/count_job_service.py` y `app/api/routes/count_jobs.py` los logs estructurados de identificador de conteo, video fuente y resultado seguro de creación.

**Checkpoint**: La creación de un trabajo de conteo es segura, aislada, asíncrona y demostrable sin implementar aún eventos o video anotado.

---

## Phase 4: User Story 2 - Consultar conteos por clase y sentido (Priority: P2)

**Goal**: El propietario consulta progreso, eventos únicos y totales incrementales por clase y dirección sin ejecutar el modelo otra vez.

**Independent Test**: Detecciones controladas con `track_id` que cambian de lado generan un solo evento con clase y dirección correctas; no-cruces, roces y recrosses no incrementan el total.

### Tests for User Story 2

- [X] T019 [P] [US2] Ampliar `tests/unit/test_line_counting.py` con pruebas de signo del producto cruzado, centro de caja, línea diagonal, cambio válido de lado, clasificación `A_to_B`/`B_to_A` y secuencias lado A → línea → lado B, inicio o fin sobre la línea.
- [X] T020 [P] [US2] Ampliar `tests/unit/test_count_job_store.py` para la unicidad por `count_job_id`/`track_id`, progreso no decreciente y agregados por clase y sentido.
- [X] T021 [P] [US2] Crear pruebas de contrato de consulta de estado y eventos paginados en `tests/contract/test_count_jobs_contract.py`.
- [X] T022 [P] [US2] Ampliar `tests/integration/test_count_job_routes.py` con progreso incremental, eventos/totales durante `processing`, aislamiento entre credenciales y cero cruces.

### Implementation for User Story 2

- [X] T023 [US2] Implementar en `app/services/line_counting.py` la determinación de lado mediante producto cruzado, conservando el último lado no nulo, y el cruce válido cuando el centro de la caja observa dos lados no nulos distintos.
- [X] T024 [US2] Implementar en `app/services/line_counting.py` la deduplicación: contar solamente el primer cambio válido por cada par `count_job_id`/`track_id`, ignorando actor estacionario, roce y recross posterior.
- [X] T025 [US2] Implementar en `app/services/count_job_store.py` el guardado transaccional de `CountEvent` con `class_id`, `class_name`, `direction`, `frame_index` no negativo y `video_time_seconds` no negativo, junto con totales agregados.
- [X] T026 [US2] Crear `app/services/count_processing.py` para leer exclusivamente `FrameDetection` y `track_id` ya almacenados del video fuente, procesarlos por fotograma y no invocar detector, tracker ni pesos del modelo.
- [X] T027 [US2] Integrar en `app/services/count_worker.py` la publicación incremental de `processed_frames`, porcentaje, eventos confirmados, totales, duración y errores seguros; comprobar cancelación y vencimiento de la fuente antes de publicar cada avance o resultado.
- [X] T028 [US2] Añadir en `app/services/count_job_service.py` las consultas autorizadas de estado, resumen y eventos paginados ordenados por fotograma, verificando propietario y TTL en cada acceso.
- [X] T029 [US2] Implementar en `app/api/routes/count_jobs.py` los endpoints `GET /v1/count-jobs/{countJobId}` y `GET /v1/count-jobs/{countJobId}/events` conforme a `specs/003-conteo-por-linea/contracts/openapi.yaml`.
- [X] T030 [US2] Añadir en `app/services/count_processing.py` logs estructurados de duración, fotogramas, cantidad de eventos y errores, sin incluir detecciones completas, rutas ni credenciales.

**Checkpoint**: El conteo entrega analítica incremental, exacta y aislada usando únicamente resultados ya disponibles del video.

---

## Phase 5: User Story 3 - Revisar el resultado visual del conteo (Priority: P3)

**Goal**: El propietario recupera un video temporal que muestra la línea, sentidos, actores rastreados y contadores coherentes con el resumen.

**Independent Test**: Un conteo completado sobre video controlado devuelve un MP4 protegido donde la línea y los totales coinciden con los eventos; un artefacto vencido no es accesible.

### Tests for User Story 3

- [X] T031 [P] [US3] Crear pruebas unitarias de superposición de línea, etiquetas de dirección y totales por clase en `tests/unit/test_count_annotation_service.py`.
- [X] T032 [P] [US3] Ampliar `tests/contract/test_count_jobs_contract.py` con el contrato de `GET /api/v1/count-jobs/{countJobId}/annotated-video` y errores de disponibilidad/vencimiento.
- [X] T033 [P] [US3] Crear pruebas de integración de acceso por propietario, eliminación por TTL y tipo `video/mp4` en `tests/integration/test_count_artifact_access.py`.

### Implementation for User Story 3

- [X] T034 [US3] Crear `app/services/count_annotation_service.py` para superponer sobre el video temporal existente la línea orientada, `A_to_B`, `B_to_A`, `track_id` y totales acumulados, sin redetectar actores.
- [X] T035 [US3] Integrar en `app/services/count_processing.py` la generación atómica del MP4 anotado temporal; comprobar que fuente y trabajo siguen vigentes/no cancelados y conservar su ruta privada solo cuando el trabajo llegue a `completed`.
- [X] T036 [US3] Añadir en `app/services/count_job_store.py` la recuperación y purga coordinada del artefacto, configuración, eventos y resumen cuando venza el video fuente, se cancele o falle el trabajo, sin publicar resultados parciales.
- [X] T037 [US3] Implementar en `app/services/count_job_service.py` y `app/api/routes/count_jobs.py` la recuperación autenticada de `/annotated-video`, sin filtrar rutas de archivos ni contenido de otro propietario.

**Checkpoint**: El resultado visual temporal está protegido, muestra evidencia coherente y desaparece con la fuente temporal.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Completar evidencia de calidad, compatibilidad contractual, rendimiento y documentación para cerrar la iteración.

- [X] T038 [P] Crear en `tests/e2e/test_line_counting_regression.py` el conjunto de al menos 10 videos controlados que demuestre 100% de primeros cruces contados una vez, no-cruces sin evento y sentidos/clases correctos.
- [X] T039 [P] Crear en `tests/performance/test_line_counting_benchmark.py` la medición reproducible de confirmación menor a dos segundos, duración, memoria, fotogramas y evidencia de cero invocaciones de inferencia.
- [X] T040 Actualizar `tests/contract/test_openapi_contract.py` y `specs/003-conteo-por-linea/contracts/openapi.yaml` para comprobar que la documentación OpenAPI publicada conserva rutas, autenticación y respuestas de conteo.
- [X] T041 Validar y documentar la ejecución de escenarios de `specs/003-conteo-por-linea/quickstart.md` en `specs/003-conteo-por-linea/quickstart.md`, incluyendo puntos inválidos, expiración, otra credencial, cero cruces y video anotado.
- [X] T042 Ejecutar `uv run pytest --cov=app --cov-report=term-missing`, resolver regresiones y registrar evidencia de cobertura, pruebas, límites y riesgos en `specs/003-conteo-por-linea/audit.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Puede empezar de inmediato.
- **Phase 2 (Foundational)**: Depende de Phase 1 y bloquea todas las historias.
- **US1 (P1)**: Depende de Phase 2. Entrega el MVP de creación segura del trabajo.
- **US2 (P2)**: Depende de US1 porque procesa los trabajos creados, aunque sus pruebas unitarias pueden prepararse en paralelo.
- **US3 (P3)**: Depende de US2 para consumir los eventos y totales finalizados.
- **Polish**: Depende de las tres historias implementadas.

### User Story Dependencies

- **US1**: No depende de otra historia; es el MVP.
- **US2**: Reutiliza `CountJob` creado por US1 y aporta progreso, eventos y totales.
- **US3**: Reutiliza el resultado de US2 para producir la evidencia visual.

## Parallel Opportunities

- En Phase 1, T001 y T002 pueden realizarse en paralelo; T003 toca el registro de aplicación.
- En Phase 2, T004, T005, T006 y T009 pueden iniciar en paralelo; T007 y T008 dependen de los modelos y almacén.
- Para US1, T010, T011 y T012 son independientes entre sí antes de T013–T018.
- Para US2, T019–T022 pueden escribirse en paralelo; T023–T030 se ejecutan en el orden de servicio, persistencia, procesamiento y rutas.
- Para US3, T031–T033 pueden escribirse en paralelo antes de la cadena T034–T037.
- T038 y T039 pueden ejecutarse en paralelo al inicio de Phase 6; T040–T042 cierran la evidencia.

## Parallel Example: User Story 2

```text
Task: "T019 Pruebas de geometría y dirección en tests/unit/test_line_counting.py"
Task: "T020 Pruebas de almacenamiento y agregados en tests/unit/test_count_job_store.py"
Task: "T021 Pruebas de contrato en tests/contract/test_count_jobs_contract.py"
Task: "T022 Pruebas de integración en tests/integration/test_count_job_routes.py"
```

## Implementation Strategy

### MVP First

1. Completar Setup y Foundational.
2. Completar US1 (T010–T018).
3. Demostrar creación autenticada y validación de una línea sobre un video terminado.
4. No continuar hasta que las pruebas de US1 estén en verde.

### Incremental Delivery

1. **US1**: Crear el trabajo seguro y asíncrono.
2. **US2**: Publicar eventos y totales incrementales sin nueva inferencia.
3. **US3**: Añadir evidencia visual temporal.
4. **Polish**: Validar los 10 videos, rendimiento, contrato, cobertura y auditoría.

## Notes

- Todas las tareas siguen el formato de lista de comprobación, identificador secuencial, marcadores de paralelismo y rutas precisas.
- `[P]` indica archivos distintos sin dependencia de tareas incompletas.
- Las tareas de pruebas se realizan primero y deben fallar antes de escribir la implementación correspondiente.
- No se incluye frontend, cámara en tiempo real, múltiples líneas, zonas, OCR, placas ni persistencia histórica.
