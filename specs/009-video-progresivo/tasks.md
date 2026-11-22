# Tasks: Video progresivo con navegación acotada

**Input**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts](contracts/README.md) y [validation-plan.md](validation-plan.md).
**Branch**: `feature/009-video-progresivo`.
**Tests**: Exigidos por criterios SC y constitución; escribir pruebas antes del comportamiento nuevo y comprobar su fallo pertinente, sin probar detalles triviales.
**Organization**: Fases por historia; no modificar el código en esta etapa. Todas las tareas empiezan pendientes.

## Formato y convenciones

Cada línea contiene ID, marcador opcional [P], historia cuando corresponde y archivo concreto. [P] permite trabajo en archivos independientes una vez cumplidos sus dependencias; no autoriza ejecutar arneses que comparten puertos al mismo tiempo.

Rutas relativas al checkout principal. No crear otro worktree, cambiar la rama, sobrescribir cambios ni usar datos privados en tests. No actualizar modelo, pesos, umbrales ni límites para aparentar rendimiento. Los archivos nuevos son destinos previstos, no resultados ya disponibles.

Las restricciones de data-model.md citadas en tareas son obligatorias, junto con todas las validaciones de los esquemas. Los gates externos permanecen abiertos si falta evidencia; completar un archivo no significa aprobar su medición.

## Phase 1: Setup

**Objetivo**: Preparar referencias y pruebas aisladas sin modificar servicios activos.

- [ ] T001 Congelar baseline 431b6df y corpus/condiciones en `specs/009-video-progresivo/validation-plan.md`; preparar manifiesto privado fuera de Git sin copiar secretos, registrar hashes/versiones y preservar el checkout principal.
- [ ] T002 [P] Añadir únicamente av==19.0.2 a `backend/pyproject.toml` y actualizar `backend/uv.lock` con Python3.12 sin actualizar modelos ni dependencias ajenas. Dep: T001.
- [ ] T003 [P] Crear fixtures deterministas CFR/VFR, B-frames, offset/edit list, rotación, vacío, denso y corto en `backend/tests/fixtures_progressive.py`, con tiempos y geometría esperados. Dep: T001.
- [ ] T004 [P] Aislar stores/puertos de prueba en `backend/tests/conftest.py` y `frontend/playwright.009.config.ts`; no usar .runtime personal ni detener servicios, conservar suites existentes. Dep: T001.

**Checkpoint**: Validar los entregables antes de continuar.

## Phase 2: Foundational

**Objetivo**: Prerrequisitos compartidos. No empezar historias hasta validar esta fase.

- [ ] T005 [P] Escribir pruebas de tipos/cronología en `backend/tests/unit/test_progressive_models.py`, con restricciones del modelo y serialización segura; deben fallar antes del soporte nuevo. Dep: T002–T004.
- [ ] T006 [P] Escribir pruebas de migración repetida, atomicidad, vacíos y carreras de publicación en `backend/tests/integration/test_progressive_store.py`, usando base temporal. Dep: T002–T004.
- [ ] T007 Implementar tipos de `backend/app/domain/models.py` y `backend/app/domain/schemas.py` según contratos: «entero de64bits» para PTS, tiempos «enteros no negativos <=2^53-1», confidence0..1 y display_bbox nullable; preservar required/enums/null de cada campo. Dep: T005.
- [ ] T008 Implementar puerto/adaptador en `backend/app/adapters/timed_video_decoder.py`: BGR24, pts/time_base, «Intervalo [start_us,end_us), end>start», lookahead, último cuadro validado y mapeo de orientación; error seguro si cronología inconsistente. Dep: T007.
- [ ] T009 Crear migración aditiva e índices en `backend/app/services/video_progressive_store.py` para entidades del modelo: «generación inmutable», «cuadros inmutables», unidad UUID y «unique(job_id,generation,track_id)»; conservar filas legacy sin reinicializar. Dep: T006–T008.
- [ ] T010 Implementar publicación transaccional en `backend/app/services/video_progressive_store.py`: cuadros vacíos, secuencia contigua, archivos cerrados, commit de límite y revisión, duplicados idempotentes y rechazo de huecos; validar TTL/revocación en la transacción. Dep: T009.
- [ ] T011 Implementar recibos de recursos en `backend/app/services/progressive_artifacts.py` con propietario, in_use y «no extensión del TTL por lectura/publicación»; purgar huérfanos sin borrar recursos ajenos. Dep: T010.
- [ ] T012 Definir parámetros operativos y validación en `backend/app/core/config.py`, sin editar .env: batch15 cuadros/0,5s, margen5s y límites de páginas/colas; distinguir timeout de duración. Dep: T007.
- [ ] T013 Ejecutar tests de fundamento y comparación decoder contra píxeles/PTS conocidos; registrar en `specs/009-video-progresivo/validation.md` discrepancias sin declararlas equivalentes ni cambiar modelo. Dep: T008–T012.

**Checkpoint**: Validar los entregables antes de continuar.

## Phase 3: User Story 1 — ver mientras procesa (P1)

**Objetivo**: Primer incremento útil: prefijo visible con pausa automática, acceso seguro y resultado final compatible.

**Prueba independiente**: Video controlado>=30s: primera vista<=2s desde cinco segundos confirmados; ningún cuadro fuera del prefijo; cola corta y vacío reproducibles.

- [ ] T014 [P] [US1] Escribir contrato de opt-in, estado/source y modo legacy en `backend/tests/contract/test_progressive_api.py`, conforme a OpenAPI; mantener respuesta202 existente. Dep: T013.
- [ ] T015 [P] [US1] Escribir prueba de arranque real con fakes en `backend/tests/integration/test_progressive_pipeline.py`: crear app, inyectar servicios, publicar antes de EOF y cerrar recursos; comprobar modelos únicos y aislamiento. Dep: T013.
- [ ] T016 [P] [US1] Escribir pruebas del estado play/pausa/espera y cola terminal en `frontend/tests/features/video-analysis/playbackReducer.test.ts`; no usar temporizadores reales para simular el análisis. Dep: T013.
- [ ] T017 [US1] Implementar presentation=progressive e idempotencia por modo en `backend/app/services/video_job_service.py` y ruta de creación; ausencia mantiene legacy, query repetida/desconocida422. Dep: T014.
- [ ] T018 [US1] Implementar estado/snapshots y páginas en `backend/app/services/video_progressive_service.py`: «from_us>=0», «to_us>from_us», ventana<=30.000.000us, snapshot>=0, cursor<=512; límites1MiB/1.000 observaciones/100 partes sin truncar, vacío confirmado. Dep: T010,T017.
- [ ] T019 [US1] Implementar fuente MP4 protegida GET/HEAD y Range en `backend/app/services/progressive_media.py`, con TTL entre bloques, no-store y referencias en uso; no limitar bytes por segundo procesado. Dep: T011,T018.
- [ ] T020 [US1] Registrar API y conectar store/servicio en `backend/app/main.py` y `backend/app/core/lifespan.py`; crear rutas en `backend/app/api/routes/video_playback.py`, inyección explícita y pruebas de arranque, sin inicializaciones globales nuevas. Dep: T018,T019.
- [ ] T021 [US1] Ampliar `backend/app/web/proxy.py` y `backend/app/web/main.py` con descriptor progressive-source, preflight propio y CSRF para JSON; conservar completed de medios legacy. Dep: T020.
- [ ] T022 [US1] Conectar único decode y lotes al `backend/app/services/video_processing.py`, sin lista ilimitada de detecciones, con PresentationFilter persistido y sin repetir carga de modelos. Dep: T008,T010,T015.
- [ ] T023 [US1] Mantener exportación final y detecciones legacy en `backend/app/services/video_job_store.py`, consumiendo observaciones persistidas y separando análisis de exportación; no reinterpretar processed-cfr/conteo. Dep: T022.
- [ ] T024 [US1] Crear parser progresivo en `frontend/src/features/video-analysis/progressiveTypes.ts` y métodos de `frontend/src/services/apiClient.ts`; validar job/generation/revision, sin cambiar parser legacy. Dep: T020.
- [ ] T025 [US1] Implementar `frontend/src/features/video-analysis/useProgressivePlayback.ts` y reducer: margen5s/tail terminal, polling500ms de una petición, intención separada de pausa y timer de vencimiento; no inventar disponibilidad. Dep: T016,T024.
- [ ] T026 [US1] Crear `frontend/src/features/video-analysis/ProgressiveVideoPlayer.tsx`: decoder silenciado no visible, admisión de píxeles/cajas por mediaTime y controles básicos; congelar salida fuera del límite, nunca mostrar original como fallback. Dep: T025.
- [ ] T027 [US1] Integrar montaje durante análisis en `frontend/src/features/video-analysis/VideoWorkspace.tsx`; progresos separados, conteo solo al completarse y cambio de modo sin perder trabajo. Dep: T021,T023,T026.
- [ ] T028 [US1] Añadir E2E de primer tramo y límite visible en `frontend/e2e/video-progressive-start.spec.ts` con backend controlado y marca temporal del commit. Dep: T027.
- [ ] T029 [US1] Añadir E2E de vacío, clip<5s y pausa manual frente a automática en `frontend/e2e/video-progressive-buffer.spec.ts`. Dep: T027.
- [ ] T030 [US1] Medir callbacks/canvas y compatibilidad en `frontend/e2e/video-progressive-render.spec.ts`, incluyendo JS ocupado y ausencia de soporte; no aprobar con solo existencia de API. Dep: T026,T028.
- [ ] T031 [US1] Verificar US1 y registrar SC001/005/006 en `specs/009-video-progresivo/validation.md`, distinguiendo pruebas controladas de gates reales pendientes. Dep: T028–T030.

**Checkpoint**: Verificar US1 con los resultados de su fase; no cerrar gates no medidos.

## Phase 4: User Story 2 — navegación acotada (P1)

**Objetivo**: Retroceder y volver al último cuadro analizado sin reinferir ni mostrar cajas antiguas.

**Prueba independiente**: Fuente120s/límite42: permitir10/30/último cuadro, bloquear60/final por todas las vías y no desplazar al crecer a55.

- [ ] T032 [P] [US2] Probar ventanas y snapshots en `backend/tests/contract/test_progressive_frames.py`: «to_us>from_us», máximo30.000.000us, cursor<=512, páginas densas divididas sin truncar. Dep: T031.
- [ ] T033 [P] [US2] Probar caché y seek en `frontend/tests/features/video-analysis/navigation.test.ts`, incluidos límite exclusivo y respuestas antiguas. Dep: T031.
- [ ] T034 [US2] Implementar LRU y ensamblado de partes en `frontend/src/features/video-analysis/frameCache.ts`:16MiB/30s acumulados, cuatro páginas en vuelo, offset/total y vacíos; recuperar historia expulsada. Dep: T032,T033.
- [ ] T035 [US2] Crear `frontend/src/features/video-analysis/VideoTimeline.tsx` con tiempos, posición/límite distinguibles sin solo color, controles táctiles y teclado. Dep: T033.
- [ ] T036 [US2] Integrar seek validado en `frontend/src/features/video-analysis/useProgressivePlayback.ts`: mantener posición al crecer límite y usar last_frame_start_us al final exclusivo, sin POST nuevo. Dep: T034,T035.
- [ ] T037 [US2] Implementar fullscreen de contenedor y tratamiento de acciones de media en `frontend/src/features/video-analysis/ProgressiveVideoPlayer.tsx`; impedir vías nativas expuestas y preservar salida canvas. Dep: T036.
- [ ] T038 [US2] Probar barra/teclado/toque/fullscreen en `frontend/e2e/video-progressive-navigation.spec.ts`, incluida ampliación200%. Dep: T037.
- [ ] T039 [US2] Medir30 saltos, al menos29<1s y memoria acotada en `frontend/e2e/video-progressive-seek.spec.ts`, con caché expulsado y sin inferencia adicional. Dep: T034,T037.
- [ ] T040 [US2] Verificar que consultas repetidas no generan trabajo de modelo en `backend/tests/integration/test_progressive_reads.py`, y que cursor ajeno o contexto distinto se rechaza. Dep: T032,T036.
- [ ] T041 [US2] Registrar aceptación US2/SC002–003 en `specs/009-video-progresivo/validation.md`, sin ocultar saltos lentos ni cambios de selección. Dep: T038–T040.

**Checkpoint**: Verificar US2 con los resultados de su fase; no cerrar gates no medidos.

## Phase 5: User Story 3 — enriquecimiento progresivo (P1)

**Objetivo**: Datos tempranos por vehículo con resultado final equivalente a la selección de evidencia vigente.

**Prueba independiente**: Al menos10 tracks, unidades pendientes/parciales y placa tardía; seleccionar/actualizar sin cambiar tiempo ni identidad y sin análisis por navegar.

- [ ] T042 [P] [US3] Escribir contratos de tracks/evidencia en `backend/tests/contract/test_progressive_tracks.py`, incluidos pending200 y propietario ajeno404. Dep: T031.
- [ ] T043 [P] [US3] Escribir pruebas top-K y deduplicación en `backend/tests/unit/test_progressive_evidence.py`, con mejor evidencia tardía y provisional excluida del consenso final. Dep: T031.
- [ ] T044 [P] [US3] Escribir pruebas de selección/revisiones en `frontend/tests/features/video-analysis/trackResults.test.tsx`. Dep: T031.
- [ ] T045 [US3] Implementar unidades y revisiones en `backend/app/services/video_progressive_store.py`, con «unique(job_id,generation,track_id)» y total abierto, sin usar ordinal detection_id. Dep: T042.
- [ ] T046 [US3] Capturar top-K/provisional antes de dibujar en `backend/app/services/progressive_evidence.py`, integrado al pipeline; conservar timestamps/bbox originales y límites por track. Dep: T043,T045.
- [ ] T047 [US3] Implementar worker progresivo y su arranque/cierre único en `backend/app/services/progressive_enrichment.py` y `backend/app/core/lifespan.py`; reutilizar modelos/semáforos,32 referencias RAM, una unidad activa y máximoK+1; no duplicar pools. Dep: T046.
- [ ] T048 [US3] Publicar ramas/resultados y agregado abierto en `backend/app/services/video_progressive_store.py`; «evaluación única por evidencia/política» y terminalización al cerrar fuente. Dep: T047.
- [ ] T049 [US3] Añadir GET tracks/detail con snapshots a `backend/app/api/routes/video_playback.py`, validando identidad y revisiones; lecturas no lanzan trabajo. Dep: T048.
- [ ] T050 [US3] Añadir PNG de evidencia autorizado a `backend/app/api/routes/video_playback.py`, con TTL, sin rutas privadas ni uso del plate-preview de imagen. Dep: T046,T049.
- [ ] T051 [US3] Ampliar allowlist de tracks/evidencia en `backend/app/web/proxy.py`, límites de respuesta y CSRF sin excepción nativa. Dep: T050.
- [ ] T052 [US3] Crear adaptador final en `backend/app/services/enrichment_job_service.py` para resultados cacheados de fuente progresiva terminada; preservar contrato y consenso legacy sin otra decodificación. Dep: T048.
- [ ] T053 [US3] Implementar consulta incremental en `frontend/src/features/video-analysis/useProgressiveTracks.ts`, snapshot estable, revisión monotónica y selección persistente. Dep: T049,T051.
- [ ] T054 [US3] Crear `frontend/src/features/video-analysis/ProgressiveTrackResults.tsx` con ficha/evidencia, selección pausada y alternativa accesible a caja, sin confundir tiempo representativo con actual. Dep: T044,T053.
- [ ] T055 [US3] Integrar enriquecimiento automático en `frontend/src/features/video-analysis/VideoWorkspace.tsx` sin POST duplicado ni espera al final para mostrar datos. Dep: T052,T054.
- [ ] T056 [US3] Probar arranque/cierre del worker, modelos únicos y ramas en `backend/tests/integration/test_progressive_enrichment.py`; verificar inyección desde la app, top-K final y liberación de recursos sin hilos ni callbacks huérfanos. Dep: T047–T052.
- [ ] T057 [US3] Añadir E2E de diez identidades y actualizaciones sin mover video en `frontend/e2e/video-progressive-tracks.spec.ts`. Dep: T055.
- [ ] T058 [US3] Verificar presupuesto de evaluaciones y reutilización final en `backend/tests/unit/test_enrichment_reuse.py`; navegar no repite lecturas. Dep: T056.
- [ ] T059 [US3] Registrar US3/SC004 y comparación de política en `specs/009-video-progresivo/validation.md`; no dar por acreditada precisión real con mocks. Dep: T057,T058.

**Checkpoint**: Verificar US3 con los resultados de su fase; no cerrar gates no medidos.

## Phase 6: User Story 4 — interrupciones y parciales (P2)

**Objetivo**: Conservar confirmados ante fallo técnico y retirar correctamente por acción explícita, acceso o vencimiento.

**Prueba independiente**: Fallo tras un tramo, desconexión, reinicio, cancelación y TTL; prefijo válido o retirada sin resurrección.

- [ ] T060 [P] [US4] Escribir fault injection de commit/archivo/revocación en `backend/tests/integration/test_progressive_lifecycle.py`. Dep: T059.
- [ ] T061 [P] [US4] Escribir pruebas de reconexión y respuestas tardías en `frontend/tests/features/video-analysis/recovery.test.ts`. Dep: T059.
- [ ] T062 [US4] Separar fallo técnico/exportación en `backend/app/services/video_worker.py` y store: partial_failed conserva prefijo, complete no se pierde por encoder. Dep: T060.
- [ ] T063 [US4] Cambiar recuperación progresiva en `backend/app/services/video_job_store.py`: no borrar ni reencolar generación interrumpida; preservar legacy sin recurso progresivo. Dep: T062.
- [ ] T064 [US4] Implementar DELETE playback idempotente y retiro de derivados en `backend/app/services/video_progressive_service.py`, incluidas carreras y tombstone propietario. Dep: T063.
- [ ] T065 [US4] Ajustar cierre/cleanup en `backend/app/services/video_artifacts.py` y `backend/app/services/temporary_cleanup.py`, sin borrado global ni extensión del plazo. Dep: T064.
- [ ] T066 [US4] Terminalizar cola tras fallo/cancelación en `backend/app/services/progressive_enrichment.py`; ningún pending indefinido ni resultado tardío revive evidencia. Dep: T062,T065.
- [ ] T067 [US4] Implementar backoff y retirada en `frontend/src/features/video-analysis/useProgressivePlayback.ts`, pausa de modo oculto y recuperación del mismo trabajo. Dep: T061,T066.
- [ ] T068 [US4] Gestionar aceptación tardía/limpieza y revocación en `frontend/src/features/video-analysis/useVideoAnalysis.ts`, diferenciando reconsulta de nuevo análisis. Dep: T067.
- [ ] T069 [US4] Añadir E2E de fallo parcial, acceso y cambio de fuente en `frontend/e2e/video-progressive-recovery.spec.ts`. Dep: T068.
- [ ] T070 [US4] Ejecutar carreras y vencimiento durante stream en `backend/tests/integration/test_progressive_lifecycle.py` y gateway; registrar fallos reproducibles. Dep: T064–T069.
- [ ] T071 [US4] Documentar US4/SC008 en `specs/009-video-progresivo/validation.md`, incluyendo limitaciones de reinicio y distinción de tiempos. Dep: T070.

**Checkpoint**: Verificar US4 con los resultados de su fase; no cerrar gates no medidos.

## Phase 7: Polish y aceptación

**Objetivo**: Regresiones, rendimiento real y validación humana antes de cierre.

- [ ] T072 Auditar rutas y logs con pruebas en `backend/tests/integration/test_progressive_security.py`: sin secretos, acceso cruzado o URLs arbitrarias. Dep: T071.
- [ ] T073 Ejecutar suites de imagen/video/conteo y compilación; registrar regresiones en `specs/009-video-progresivo/validation.md`, sin retirar tests ni tocar datos personales. Dep: T072.
- [ ] T074 Crear `backend/scripts/evaluate_video_progressive.py` según protocolo congelado, con ambos brazos aislados y todos los resultados, no solo éxitos. Dep: T073.
- [ ] T075 Ejecutar tres pares AB/BA reales y comparar calidad/PTS/identidades y coste en `specs/009-video-progresivo/validation.md`; gates110% tiempo y120% RSS, sin alterar corpus ni tratar fallos como mejoras. Dep: T074.
- [ ] T076 Medir SC001–006 en navegadores y tamaños previstos con `frontend/e2e/video-progressive-render.spec.ts`; reportar esperas separadas de FPS y desfase. Dep: T073.
- [ ] T077 Realizar prueba con cinco participantes y registrar SC009 en `specs/009-video-progresivo/usability.md`; si no hay participantes, mantener pendiente y no simular evidencia. Dep: T076.
- [ ] T078 Actualizar guía de arranque/limitaciones en `specs/009-video-progresivo/quickstart.md` y README, sin publicar configuración privada. Dep: T073.
- [ ] T079 Consolidar matriz FR/SC y evidencia en `specs/009-video-progresivo/audit.md`, manteniendo pendientes de otras iteraciones y gates no ejecutados. Dep: T075–T078.
- [ ] T080 Verificar quickstart y estado final en `specs/009-video-progresivo/validation.md`; conservar rama/cambios existentes y confirmar solo entrega pertinente, sin declarar aceptación si quedan gates. Dep: T079.

**Checkpoint**: Validar los entregables antes de continuar.

## Dependencies & Execution Order

Setup → fundamentos → US1. US2 y US3 se integran después de US1, y pueden prepararse con fixtures independientes sin editar los mismos archivos. US4 depende de recursos de US1 y unidades de US3; la aceptación final incluye todas las historias.

- T001 precede a T002–T004; fundamentos dependen de setup.
- Dentro de cada fase, las dependencias indicadas tienen prioridad sobre el orden aparente. Las pruebas se escriben antes y se ejecutan cuando exista el comportamiento.
- Paquetes del plan: B1=T005–T013/T022; B2=T017–T023 y ciclo de vida US4; B3/B4=US3; G1=T021/T051; F1/F2=US1/US2/US3; V1=verificación por historia y fase final.
- El MVP demostrable es US1 con fundamento seguro. No equivale a cierre de la iteración ni autoriza omitir recuperación, enriquecimiento o gates finales.

### Grafo de dependencias

```mermaid
flowchart LR
  Setup --> Fundamentos
  Fundamentos --> US1
  US1 --> US2
  US1 --> US3
  US3 --> US4
  US2 --> ValidacionFinal
  US4 --> ValidacionFinal
```

## Oportunidades paralelas

| Fase | Trabajo independiente | Límite |
|---|---|---|
| Setup | T002,T003,T004 tras T001 | dependencias, fixtures y aislamiento en archivos distintos |
| US1 | T014,T015,T016 tras fundamento | pruebas diferentes; integrar antes de completar la fase |
| US2 | T032,T033 | contrato y estado cliente; ejecución de navegador aislada |
| US3 | T042,T043,T044 | contratos, evidencia y componentes con fixtures |
| US4 | T060,T061 | fallos de backend y recuperación de frontend |

No paralelizar cambios sobre el mismo store/reducer ni benchmark con otras cargas. Esto describe oportunidades; no exige múltiples agentes.

## Estrategia incremental

1. Fijar baseline y completar fundamentos.
2. Entregar y validar US1 en entorno de prueba.
3. Añadir navegación US2 y enriquecimiento US3, manteniendo pruebas anteriores.
4. Completar recuperación/retiro US4.
5. Ejecutar regresiones y mediciones reales, prueba humana y auditoría. Registrar bloqueos, no marcar tareas externas por suposición.
6. Confirmar incrementos coherentes con sus archivos y conservar trabajo ajeno.

### Ejemplos por historia

- US1: T014, T015 y T016 escriben pruebas en archivos distintos tras los fundamentos.
- US2: T032 y T033 separan contrato de ventanas y estado del cliente.
- US3: T042, T043 y T044 separan contratos, evidencia y selección visual.
- US4: T060 y T061 separan fallos de backend y recuperación del cliente tras US3.

La ejecución en paralelo es opcional; los cambios que comparten archivo se realizan secuencialmente.

## Integración de arranque

T020 conecta los componentes al ciclo de vida de la app; T047 añade el worker al mismo contenedor de dependencias. T015 y T056 prueban el recorrido de arranque/cierre, sin cargar modelos reales ni duplicarlos. Los IDs se conservan.

## Trazabilidad

| Requisito | Tareas |
|---|---|
| FR-001 | T017,T018,T022,T027,T028 |
| FR-002 | T007,T009,T010,T018 |
| FR-003 | T010,T032,T060 |
| FR-004 | T026,T036,T037,T038 |
| FR-005 | T034,T036,T039,T040 |
| FR-006 | T027,T035 |
| FR-007 | T025,T029 |
| FR-008 | T025,T029 |
| FR-009 | T008,T026,T030 |
| FR-010 | T022,T026,T037 |
| FR-011 | T023,T027,T052 |
| FR-012 | T046,T047,T055 |
| FR-013 | T047,T052,T058 |
| FR-014 | T054,T055,T057 |
| FR-015 | T048,T054,T056 |
| FR-016 | T027,T071,T078 |
| FR-017 | T067,T068,T069 |
| FR-018 | T062,T063,T066,T070 |
| FR-019 | T064,T065,T068 |
| FR-020 | T019,T021,T050,T051,T072 |
| FR-021 | T035,T054,T076,T077 |
| FR-022 | T001,T013,T074,T075,T076 |
| FR-023 | T023,T052,T073 |

| Criterio | Verificación |
|---|---|
| SC001 | T028,T031,T076 |
| SC002 | T038,T076 |
| SC003 | T039 |
| SC004 | T057,T059 |
| SC005 | T013,T030,T076 |
| SC006 | T030,T076 |
| SC007 | T074,T075 |
| SC008 | T069,T070,T072 |
| SC009 | T077 |
| SC010 | T039,T075 |

## Cierre de esta generación

80 tareas pendientes. US1:18, US2:10, US3:18, US4:12; setup/fundamento/cierre:22. Formato y referencias comprobables antes del commit. Las tareas de ejecución no se marcan completas al generar esta lista.
