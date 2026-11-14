---

description: "Tareas implementables para extracción de características y placas"
---

# Tasks: Extracción de características y placas

**Input**: Artefactos de diseño de `specs/004-extraccion-caracteristicas-y-placas/`.

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/openapi.yaml` y `quickstart.md`.

**Tests**: Obligatorios por la constitución, los criterios de aceptación y el plan. Escribir cada prueba antes de la implementación que valida; usar adaptadores falsos en la suite ordinaria y reservar los modelos reales para smoke/E2E controlados.

**Organization**: Las tareas se agrupan por historia de usuario para que cada incremento se pueda construir, probar y demostrar independientemente. No incluye frontend.

## Phase 1: Setup (Infraestructura compartida)

**Purpose**: Declarar dependencias reproducibles, configuración externa y fixtures controladas antes de incorporar modelos o datos sensibles.

- [ ] T001 Añadir en `pyproject.toml` las dependencias explícitas y versiones reproducibles para PaddleOCR/PaddlePaddle y el cargador compatible con el checkpoint EfficientNet-B1, sin depender de instalaciones transitivas de Ultralytics.
- [ ] T002 [P] Añadir en `app/core/config.py` y `.env.example` rutas externas de pesos/manifiesto, directorios privados, límites de cola/concurrencia, TTL, lista de clases vehiculares, máximo de evidencia por track y umbrales de localización, reintento y aceptación OCR.
- [ ] T003 [P] Crear en `tests/enrichment_fixtures.py` imágenes, detecciones, tracks, lecturas OCR y API keys sintéticas; no incluir matrículas reales ni pesos en el repositorio.
- [ ] T004 [P] Crear el manifiesto de ejemplo y validador de configuración en `specs/004-extraccion-caracteristicas-y-placas/model-manifest.example.yaml` para arquitectura, etiquetas, entrada, normalización, umbrales, versión y checksum del EfficientNet-B1.

---

## Phase 2: Foundational (Prerrequisitos bloqueantes)

**Purpose**: Construir contratos de dominio, fuentes temporales privadas, persistencia y ciclo de vida que bloquean todas las historias.

**⚠️ CRITICAL**: No iniciar una historia de usuario antes de completar esta fase.

- [ ] T005 [P] Extender `app/domain/models.py` con `EnrichmentJobStatus`, `EnrichmentJob`, `EnrichmentUnit`, `AttributeResult`, `PlateResult`, `PlateCandidate` y transiciones `queued → processing → completed`; permitir `failed` o `cancelled` solo desde estados no terminales.
- [ ] T006 [P] Extender `app/domain/schemas.py` con DTOs del contrato: fuente `image|video`, creación, estado/progreso, resultado paginado, atributos, caja relativa y placa con estados `read`, `unreadable`, `not_detected` o `failed`.
- [ ] T007 [P] Crear protocolos tipados y falsos de prueba en `app/adapters/attribute_extractor_protocol.py`, `app/adapters/plate_localizer_protocol.py`, `app/adapters/plate_reader_protocol.py` y `tests/enrichment_fixtures.py`.
- [ ] T008 Crear `app/services/source_artifacts.py` para almacenar originales y variantes con nombres no predecibles, rutas privadas y eliminación idempotente; nunca devolver una ruta local ni URL pública de recorte.
- [ ] T009 Crear `app/services/image_detection_store.py` con una fuente temporal que cumpla: `source_id` UUID, `owner_key_id` obligatorio, imagen original privada, dimensiones/medio validados, detecciones con `detection_id` estable y `expires_at` no posterior a `ARTIFACT_TTL_SECONDS`.
- [ ] T010 Actualizar `app/services/detection_service.py`, `app/api/routes/detections.py` y `app/services/temporary_artifacts.py` para asociar el principal autenticado, conservar el original/detecciones de imagen y proteger también la imagen anotada por propietario hasta su vencimiento.
- [ ] T011 Actualizar `app/services/video_processing.py`, `app/services/video_job_store.py` y `app/services/video_artifacts.py` para conservar la entrada original de un `VideoJob` terminado solo hasta su TTL, sin romper la limpieza de videos anotados existentes.
- [ ] T012 Crear `app/services/enrichment_job_store.py` con SQLite, índices por propietario/vencimiento y tablas para trabajos, unidades, atributos, placas y candidatos; imponer un `track_id` consolidado por trabajo y `expires_at = min(vencimiento fuente, ENRICHMENT_RESULT_TTL_SECONDS)`.
- [ ] T013 Crear `app/services/enrichment_job_service.py` y `app/services/enrichment_worker.py` como cola temporal recuperable: reencolar `processing` vigente tras reinicio y purgar resultados/fuentes vencidos sin texto, recortes ni rutas residuales.
- [ ] T014 Integrar configuración, almacenes, adaptadores cargados una vez, límites por modelo, trabajador y limpieza en `app/core/lifespan.py`; registrar `ready` solo después de smoke checks no sensibles de componentes configurados.
- [ ] T015 Crear `app/api/routes/enrichment_jobs.py`, registrarlo en `app/main.py` bajo `/api` y ampliar `app/api/error_handlers.py` con errores seguros para fuente no apta, cola llena, modelo no disponible y resultado vencido.
- [ ] T016 [P] Crear pruebas unitarias de configuración/manifiesto y de persistencia/TTL/transiciones en `tests/unit/test_enrichment_config.py` y `tests/unit/test_enrichment_job_store.py`.
- [ ] T017 [P] Crear pruebas de integración de retención privada de imagen/video, recuperación tras reinicio y aislamiento de la imagen anotada en `tests/integration/test_enrichment_source_access.py`.

**Checkpoint**: Dominio, fuentes originales privadas, modelos inicializables, cola y aislamiento por propietario están disponibles sin exponer placa ni rutas internas.

---

## Phase 3: User Story 1 - Enriquecer detecciones existentes de vehículos (Priority: P1) 🎯 MVP

**Goal**: Un usuario autorizado crea y consulta un trabajo temporal para una imagen vigente o video terminado propio, reutilizando exclusivamente detecciones existentes.

**Independent Test**: Con fuente de imagen o video `completed`, vigente y del propietario, `POST /api/v1/enrichment-jobs` devuelve `202` en menos de dos segundos y `GET` publica estado/progreso; fuentes inexistentes, ajenas, vencidas, no terminadas o sin vehículos no crean trabajo.

### Tests for User Story 1

- [ ] T018 [P] [US1] Crear pruebas de contrato para `POST /api/v1/enrichment-jobs`, `GET /api/v1/enrichment-jobs/{enrichmentJobId}` y `DELETE` con respuestas `202`, `400`, `401`, `404`, `409`, `410` y `503` en `tests/contract/test_enrichment_contract.py`.
- [ ] T019 [P] [US1] Crear pruebas unitarias para elegibilidad de clase, recorte acotado y rechazo de caja vacía/fuera del marco en `tests/unit/test_vehicle_cropping.py`.
- [ ] T020 [P] [US1] Crear pruebas de integración de fuentes `image|video`, propietario, vencimiento, `completed`, cero vehículos y confirmación menor a dos segundos en `tests/integration/test_enrichment_job_routes.py`.

### Implementation for User Story 1

- [ ] T021 [US1] Crear `app/services/vehicle_cropping.py` para aceptar solo clases de la lista vehicular configurable y formar un recorte acotado al marco con ancho y alto mayores que cero, sin invocar el detector vial base.
- [ ] T022 [US1] Implementar en `app/services/enrichment_job_service.py` la resolución autorizada de `SourceReference`: imagen vigente o video `completed` y vigente, con errores indistinguibles para recurso inexistente o ajeno.
- [ ] T023 [US1] Implementar en `app/services/enrichment_job_store.py` la creación atómica de trabajo/units: UUID público, propietario, estado `queued`, total elegible, progreso no decreciente y TTL mínimo de la fuente/límite configurado.
- [ ] T024 [US1] Implementar en `app/services/enrichment_worker.py` el avance de `queued` a `processing`, cancelación segura, recuperación y progreso por unidad; impedir publicar si la fuente vence durante el cálculo.
- [ ] T025 [US1] Implementar en `app/api/routes/enrichment_jobs.py` creación, consulta y cancelación autenticadas según `specs/004-extraccion-caracteristicas-y-placas/contracts/openapi.yaml`, sin bloquear hasta terminar la inferencia.
- [ ] T026 [US1] Registrar en `app/services/enrichment_job_service.py` y `app/services/enrichment_worker.py` identificador de solicitud, fuente, vehículos elegibles, estado, latencia y vencimiento, sin caja completa, rutas, credenciales ni texto de placa.

**Checkpoint**: El MVP acepta y administra un trabajo seguro de enriquecimiento sobre fuentes existentes, sin volver a detectar actores viales.

---

## Phase 4: User Story 2 - Consultar características visuales (Priority: P2)

**Goal**: El propietario consulta atributos, etiquetas y confianzas del catálogo aprobado para cada vehículo de imagen o resultado consolidado de video.

**Independent Test**: Con un extractor falso y recortes controlados, cada vehículo publica `attribute_name`, `label`, confianza entre 0 y 1 y referencia de detección; un fallo de atributos no borra la rama de placa.

### Tests for User Story 2

- [ ] T027 [P] [US2] Crear pruebas unitarias de carga/validación del manifiesto —arquitectura, etiquetas, entrada, normalización, umbrales y checksum— en `tests/unit/test_attribute_manifest.py`.
- [ ] T028 [P] [US2] Crear pruebas unitarias de selección de evidencia de mayor calidad/confianza y un solo resultado por `track_id` en `tests/unit/test_track_consolidation.py`.
- [ ] T029 [P] [US2] Crear pruebas de integración de atributos exitosos, recorte inválido, fallo aislado de extractor y asociación fuente/detección/fotograma en `tests/integration/test_enrichment_attributes.py`.

### Implementation for User Story 2

- [ ] T030 [US2] Implementar `app/adapters/efficientnet_attribute_extractor.py` contra `AttributeExtractor`, usando únicamente manifiesto y pesos externos; cargar el modelo una vez y devolver etiquetas del catálogo aprobado.
- [ ] T031 [US2] Crear la selección de candidatos por track en `app/services/track_consolidation.py`, con máximo configurable de fotogramas de evidencia y sin afirmar identidad real fuera del seguimiento existente.
- [ ] T032 [US2] Implementar en `app/services/enrichment_processing.py` la rama de atributos: recorte válido, inferencia acotada, atributo/etiqueta/confianza, fotograma de evidencia y estado `completed|failed` por unidad.
- [ ] T033 [US2] Implementar en `app/services/enrichment_job_store.py` la persistencia de `AttributeResult` con clave única `(unit_id, attribute_name)`, confianza finita entre 0 y 1 y manifiesto/versiones no secretas.
- [ ] T034 [US2] Integrar en `app/services/enrichment_worker.py` la ejecución independiente de atributos con semáforo del modelo y la conservación de resultados aun cuando la rama de placa falle.
- [ ] T035 [US2] Implementar en `app/services/enrichment_job_service.py` y `app/api/routes/enrichment_jobs.py` la paginación de resultados conforme al contrato, con atributos, referencia de detección y `evidence_frame_indexes` sin revelar recortes.

**Checkpoint**: Los atributos del modelo aprobado se entregan por vehículo/track con trazabilidad, aislamiento y tolerancia al fallo de la otra rama.

---

## Phase 5: User Story 3 - Consultar placas de forma protegida (Priority: P2)

**Goal**: El propietario obtiene ubicación, estado y texto de placa únicamente cuando hay evidencia suficiente; el sistema rechaza lecturas dudosas sin inventar caracteres.

**Independent Test**: Con adaptadores falsos de placa legible, ilegible y ausente, la API devuelve `read`, `unreadable` y `not_detected`; el texto aparece solo con `read` y otra API key no puede acceder a ningún dato de placa.

### Tests for User Story 3

- [ ] T036 [P] [US3] Crear pruebas unitarias de selección de caja de placa de mayor confianza, coordenadas relativas y estados `not_detected|unreadable|read` en `tests/unit/test_plate_processing.py`.
- [ ] T037 [P] [US3] Crear pruebas unitarias del OCR original, umbral de baja confianza, rectificación/mejora conservadora, un único reintento y prohibición de autocorrección por patrón en `tests/unit/test_plate_quality.py`.
- [ ] T038 [P] [US3] Crear pruebas unitarias de consenso ponderado por calidad/localización/OCR, desacuerdo e insuficiencia de evidencia por `track_id` en `tests/unit/test_plate_consensus.py`.
- [ ] T039 [P] [US3] Crear pruebas de integración de resultados protegidos, aislamiento por API key, omisión de texto para estados no `read` y ausencia de matrículas/rutas en logs en `tests/integration/test_enrichment_plate_access.py`.

### Implementation for User Story 3

- [ ] T040 [US3] Implementar `app/adapters/yolov8_plate_localizer.py` contra `PlateLocalizer`, cargando una vez los pesos externos YOLOv8n y devolviendo una única candidata de mayor confianza dentro del recorte vehicular.
- [ ] T041 [US3] Implementar `app/adapters/paddle_plate_reader.py` contra `PlateReader`, con directorio/modelo/idioma/dispositivo externos y retorno de texto más `rec_score` sin registrar el texto.
- [ ] T042 [US3] Implementar `app/services/plate_quality.py` para validar calidad, rectificar orientación/perspectiva y aplicar únicamente contraste, reducción de ruido, nitidez y escalado conservador cuando el OCR original quede bajo `PLATE_OCR_RETRY_THRESHOLD`.
- [ ] T043 [US3] Implementar en `app/services/enrichment_processing.py` la rama de placa: localización, OCR original, un único reintento, umbral `PLATE_OCR_ACCEPT_THRESHOLD`, artefactos temporales privados y estados seguros sin completar caracteres por formato.
- [ ] T044 [US3] Implementar `app/services/plate_consensus.py` para consolidar por `track_id` lecturas válidas ponderadas por calidad, confianza del localizador y OCR; devolver `unreadable` ante desacuerdo o evidencia insuficiente.
- [ ] T045 [US3] Implementar en `app/services/enrichment_job_store.py` la persistencia temporal de candidatos y `PlateResult`, permitiendo `plate_text` solo con estado `read` y purgándolo junto con sus variantes/recortes.
- [ ] T046 [US3] Integrar en `app/services/enrichment_worker.py` la rama de placa en paralelo, con semáforo independiente, y conservar la rama de atributos cuando la placa falle o viceversa.
- [ ] T047 [US3] Actualizar `app/domain/schemas.py`, `app/services/enrichment_job_service.py` y `app/api/routes/enrichment_jobs.py` para devolver caja relativa, confianzas, evidencia y texto exclusivamente al propietario y solo con `plate.status=read`.

**Checkpoint**: La lectura de placa es privada, temporal, respaldada por confianza/consenso y no transforma una duda de OCR en una matrícula afirmada.

---

## Phase 6: User Story 4 - Consultar resultados temporales y auditables (Priority: P3)

**Goal**: El propietario consulta resultados parciales válidos y estados de fallo seguros mientras existan; al vencer se elimina acceso y evidencia sensible.

**Independent Test**: Al fallar una rama se conserva la otra; al cancelar o expirar fuente/trabajo no quedan resultados, recortes o texto recuperables y se responde con el estado seguro correspondiente.

### Tests for User Story 4

- [ ] T048 [P] [US4] Crear pruebas de integración de fallo aislado de rama, cancelación, vencimiento durante proceso, `410` y limpieza de archivos en `tests/integration/test_enrichment_cleanup.py`.
- [ ] T049 [P] [US4] Crear pruebas de contrato para listado paginado de `/results`, estados seguros y campos sensibles condicionales en `tests/contract/test_enrichment_contract.py`.

### Implementation for User Story 4

- [ ] T050 [US4] Implementar en `app/services/enrichment_job_store.py` publicación atómica: no publicar resultados parciales si la fuente vence, eliminar candidatos/placas/recortes al cancelar, fallar o expirar y conservar solo marcador mínimo para `410` del propietario.
- [ ] T051 [US4] Implementar en `app/services/enrichment_job_service.py` la consulta autorizada y paginada de resultados disponibles, con progreso y errores genéricos que no revelen modelo, ruta, fuente ajena ni texto sensible.
- [ ] T052 [US4] Añadir en `app/services/enrichment_worker.py` y `app/core/logging.py` métricas estructuradas por trabajo/rama: latencia, p50/p95, memoria, errores, reintentos, candidatos y consenso; excluir textos de placa, imágenes, rutas y secretos.
- [ ] T053 [US4] Actualizar `app/core/lifespan.py` y `app/services/source_artifacts.py` para ejecutar limpieza coordinada de fuente, resultados y artefactos de enriquecimiento al finalizar, reiniciar y vencer TTL.

**Checkpoint**: Resultados útiles permanecen disponibles solo para su propietario mientras son vigentes y dejan evidencia de operación sin filtrar datos sensibles.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Validar contratos, calidad de modelos, seguridad, rendimiento y evidencia final de la iteración.

- [ ] T054 [P] Ampliar `tests/contract/test_openapi_contract.py` para comparar la OpenAPI publicada con `specs/004-extraccion-caracteristicas-y-placas/contracts/openapi.yaml`, autenticación y respuestas sensibles condicionales.
- [ ] T055 [P] Crear smoke tests opt-in de EfficientNet-B1, YOLOv8n de placas y PaddleOCR configurados en `tests/e2e/test_enrichment_model_smoke.py`, sin ejecutar pesos reales en CI ordinario.
- [ ] T056 [P] Crear evaluación E2E de al menos 20 recortes y 10 tracks en `tests/e2e/test_enrichment_regression.py`: asociación correcta, atributos, placas `read|unreadable|not_detected`, un registro por track y consenso sin autocorrección.
- [ ] T057 [P] Crear benchmark reproducible en `tests/performance/test_enrichment_reference_benchmark.py` para confirmación menor a dos segundos, p50/p95 por rama/track, memoria, errores y carga única de modelos.
- [ ] T058 Documentar en `specs/004-extraccion-caracteristicas-y-placas/model-evaluation.md` el conjunto autorizado, hardware, manifiestos, macro F1, AP/IoU, exactitud OCR, CER, tasa de lectura falsa y comparación original/reintento/consenso con línea base aprobada.
- [ ] T059 Actualizar `specs/004-extraccion-caracteristicas-y-placas/quickstart.md` con evidencia ejecutada de fuentes de imagen/video, aislamiento, vencimiento, baja confianza y desacuerdo de placas.
- [ ] T060 Ejecutar `uv run pytest --basetemp .pytest-tmp-enrichment --cov=app --cov-report=term-missing`, resolver regresiones y registrar pruebas, cobertura, métricas, riesgos y pendientes en `specs/004-extraccion-caracteristicas-y-placas/audit.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Puede iniciar de inmediato.
- **Phase 2 (Foundational)**: Depende de Setup y bloquea todas las historias.
- **US1 (P1)**: Depende de Foundation; entrega el MVP de crear y consultar trabajo seguro.
- **US2 (P2)** y **US3 (P2)**: Dependen de US1 y pueden implementarse en paralelo tras estabilizar el modelo de resultados compartido.
- **US4 (P3)**: Depende de US2 y US3 para probar fallos cruzados, retención y resultados parciales seguros.
- **Polish**: Depende de las cuatro historias.

### User Story Dependencies

- **US1**: No depende de otra historia; crea el trabajo y resuelve fuentes/restricciones.
- **US2**: Añade atributos a las unidades creadas por US1.
- **US3**: Añade localización y OCR de placa a las mismas unidades; no depende de la inferencia de atributos.
- **US4**: Comprueba publicación, vencimiento y auditoría de ambas ramas.

## Parallel Opportunities

- Setup: T002, T003 y T004 pueden avanzar en paralelo después de T001.
- Foundation: T005–T007 y T016–T017 pueden avanzar en paralelo; T008–T015 se integran según sus dependencias de fuente/almacén/ciclo de vida.
- US1: T018–T020 se escriben en paralelo antes de T021–T026.
- US2: T027–T029 se escriben en paralelo; T030 y T031 pueden comenzar en paralelo, seguidas por T032–T035.
- US3: T036–T039 se escriben en paralelo; T040 y T041 pueden comenzar en paralelo, seguidas por T042–T047.
- Polish: T054–T057 pueden prepararse en paralelo; T058–T060 consolidan la evidencia.

## Parallel Example: User Story 3

```text
Task: "T036 Estados y caja relativa en tests/unit/test_plate_processing.py"
Task: "T037 Reintento único y no-autocorrección en tests/unit/test_plate_quality.py"
Task: "T038 Consenso por track en tests/unit/test_plate_consensus.py"
Task: "T039 Aislamiento y logs seguros en tests/integration/test_enrichment_plate_access.py"
```

## Implementation Strategy

### MVP First

1. Completar Setup y Foundation.
2. Completar US1 (T018–T026).
3. Demostrar creación/consulta protegida sobre una imagen y un video propios, sin reinferencia vial.
4. Detenerse y validar pruebas de US1 antes de cargar modelos reales.

### Incremental Delivery

1. **US1**: Fuentes y trabajo temporal seguros.
2. **US2**: Atributos del EfficientNet-B1 con manifiesto reproducible.
3. **US3**: Placas con OCR seguro, reintento conservador y consenso de video.
4. **US4**: Vencimiento, tolerancia a fallos y observabilidad.
5. **Polish**: Evidencia de modelos, contrato, rendimiento, cobertura y auditoría.

## Notes

- Todas las tareas siguen el formato de lista de comprobación, identificador secuencial, marcadores de paralelismo y rutas precisas.
- `[P]` indica archivos distintos sin dependencia de tareas incompletas.
- Las pruebas se realizan primero y deben fallar antes de escribir la implementación correspondiente.
- Los pesos, manifiestos, placas reales y `.env` no se agregan al repositorio.
