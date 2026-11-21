# Tasks: Exploración visual de imágenes viales enriquecidas

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md).
**Branch**: `feature/006-mejoras-frontend`.
**Checkout**: `C:/Users/USER/Desktop/Mateo/GESTIÓN DE PROYECTOS`.
**Prerequisites**: Plan aprobado, incluidos backend B1–B5. Preservar los cambios existentes y las referencias de rama corregidas en documentación. No cambiar de rama, restaurar archivos ni incorporar CSV ajenos.
**Tests**: Solicitadas expresamente. Escribir pruebas antes del comportamiento correspondiente y confirmar que detectan el caso corregido. Crearlas no equivale a ejecutarlas.
**Organization**: Setup → fundamentos compartidos → cinco historias priorizadas → verificación transversal.

## Format: `[ID] [P?] [Story] Description`

- `[P]` permite coincidir con tareas del mismo grupo independiente sobre archivos distintos, una vez cumplidas sus dependencias. No autoriza concurrencia sobre store/worker/lifespan ni implica lanzar agentes.
- `[US1]` a `[US5]` identifican historias de la especificación; setup, fundamentos y cierre no llevan historia.
- Rutas relativas al checkout principal. Reutilizar dependencias/adaptadores; sin modelos, pesos, umbrales nuevos, seguimiento ficticio ni rediseño de video.
- `contracts/backend-additions.md` define el comportamiento; el OpenAPI de 006 es una extensión, no un reemplazo del contrato completo.

## Phase 1: Setup — herramientas y evidencia de prueba

**Purpose**: Preparar pruebas reproducibles y fixtures sintéticos sin introducir simulaciones en producción.

- [X] T001 Configurar Vitest/jsdom y Testing Library en `frontend/vite.config.ts`, `frontend/tests/setup.ts` y, solo si es necesario conectar scripts, `frontend/package.json`; conservar versiones y lockfile salvo cambio imprescindible documentado.
- [X] T002 [P] Configurar Chromium, viewports 360/768/1440 y arranque de servidores en `frontend/playwright.config.ts`; separar recorrido integrado de capturas con fixtures y no depender de un servidor personal ya abierto.
- [X] T003 [P] Crear fixtures sintéticos con cuadrantes de color, EXIF 1–8, actores mixtos, cajas inválidas/solapadas y más de 50 resultados en `tests/image_exploration_fixtures.py` y `frontend/tests/fixtures/imageAnalysis.ts`; incluir placa legible/ilegible/ausente/fallida y texto canario no sensible para redacción.
- [X] T004 Crear servidor determinista en `tests/e2e/serve_frontend_test_api.py`, reutilizando `tests/conftest.py`, `tests/enrichment_fixtures.py` y `app.main.create_app`; inyectar adaptadores solo desde pruebas, con almacenamiento/configuración sintéticos aislados, sin cargar pesos privados para verificar UI.

**Checkpoint**: Herramientas y fixtures coherentes con contratos, disponibles para las siguientes fases.

## Phase 2: Foundational — backend B1/B2/B4/B5 y cliente compartido

**Purpose**: Resolver identidad, geometría, evidencia y seguridad compartidas. T005/T006 anteceden B1/B2; T013/T014 anteceden B4/B5.

### B1 y B2: imagen canónica y evidencia protegida

- [X] T005 [P] Añadir pruebas EXIF 1–8, RGB, dimensiones/cajas/crops en `tests/unit/test_image_geometry.py` y `tests/unit/test_image_validation.py`; crear `tests/unit/test_inference_observability.py` con adaptadores sintéticos para detección y ramas de enriquecimiento, verificando duración, RSS inicial/final/máximo muestreado, correlación y finalización ante fallo/cancelación/vencimiento sin secretos o placas en logs; preservar video válido y límites de upload.
- [X] T006 [P] Añadir pruebas del contrato aditivo, elegibilidad y original protegido en `tests/contract/test_detection_contract.py`, `tests/contract/test_openapi_contract.py` y `tests/integration/test_canonical_image_access.py`; cubrir 200 PNG, 401, 404 ajeno/desconocido, 410 solo del dueño vencido, ausencia de rutas privadas y `Cache-Control: no-store`. Validar que POST imagen y GET readiness estén enlazados a sus esquemas y que todas las referencias locales se resuelvan y sean alcanzables desde operaciones.
- [X] T007 Implementar geometría compartida en `app/services/image_geometry.py`: «enteros, origen superior izquierdo, intervalos semiabiertos `[x_min,x_max) × [y_min,y_max)`», «0 <= x_min < x_max <= width» y «0 <= y_min < y_max <= height»; truncar/limitar igual en todas las capas y descartar degeneradas antes de asignar IDs, sin fabricar un píxel.
- [X] T008 Normalizar una sola vez en `app/services/image_validation.py`: «PNG canónico con orientación aplicada y RGB; no conserva EXIF/GPS» y «Enteros >0 de los píxeles canónicos usados por detección, anotación y enriquecimiento»; validar MIME/extensión/tamaño originales antes de normalizar, conservar límite de píxeles/control de recursos y usar la API compatible con Pillow instalado.
- [X] T009 Integrar píxeles/cajas canónicos en `app/services/detection_service.py`, `app/services/image_detection_store.py`, `app/services/annotation_service.py` y `app/services/vehicle_cropping.py`; misma colección e IDs una vez, «No renumerar al filtrar vehículos ni al paginar». Crear el contexto común de medición en `app/services/inference_metrics.py` y campos seguros en `app/core/logging.py`: duración por etapas, RSS del proceso memory_mb y máximo muestreado peak_memory_mb, muestras inicial/final y cada 100 ms en operaciones largas, resultado/error_code e identidad, sin atribuir memoria exclusiva a jobs concurrentes ni inventar frame_ms para imagen; conservar métricas y geometría válidas de video.
- [X] T010 Ampliar `app/domain/schemas.py` con `source_expires_at`, `original_image` y `enrichment_eligible` conservando campos anteriores; aplicar «detection_id>=1», «class_id>=0», «class_name no vacío», «confidence entre 0 y 1» y cajas estrictas de T007; descriptor URL relativa, media_type=image/png y expires_at; «track_id: null/ausente para imagen estática» y elegibilidad «booleano calculado por el servidor con su conjunto de clases, no una lista rígida del cliente».
- [X] T011 Coordinar vigencia/acceso en `app/services/image_detection_store.py`, `app/services/temporary_artifacts.py` y `app/services/source_artifacts.py`: «Fecha UTC efectiva común a original/anotación/fuente o mínimo publicado explícitamente. No ampliar TTL al leer/reintentar» y «Ruta privada que nunca se serializa»; tombstones mínimos por dueño, lectura/borrado coordinados y sin revelar vencimientos de otro propietario.
- [X] T012 Implementar GET `/api/v1/detections/{requestId}/original-image` en `app/api/routes/detections.py` y metadatos desde `app/services/detection_service.py`, reutilizando la fuente almacenada; misma autenticación/propiedad/TTL, 404 ajeno, 410 del dueño, no-store y errores seguros también en evidencia afectada, sin endpoints separados de crop ni otra copia del upload.

### B4 y B5: integridad y ciclo de vida

- [X] T013 [P] Añadir pruebas de saneamiento en `tests/unit/test_enrichment_results.py` y `tests/unit/test_enrichment_job_store.py`: texto canario no read ausente en JSON/tablas/resultado servido, confianzas y estados coherentes, asociación correcta y localización conservada tras fallo OCR.
- [X] T014 [P] Añadir pruebas con barreras/reloj controlado en `tests/unit/test_enrichment_lifecycle.py` y `tests/integration/test_enrichment_lifecycle.py`: cancel/finish, fail/finish, TTL/finish, cancelación en cola, worker tardío, purga sin solicitudes y cierre del janitor; impedir resurrección de datos y cambios entre estados terminales, sin sleeps largos.
- [X] T015 Crear saneamiento común en `app/services/enrichment_results.py` y validación en `app/domain/schemas.py`: «plate.status: read/unreadable/not_detected/failed», «Texto permitido solo read; en todos los demás, text=null o ausente en cualquier representación», «confianza 0–1» y «plate.bbox_relative: 0–1, orden estricto entre extremos; normalizado respecto al crop vehicular canónico, nunca la imagen completa»; conservar bbox/localizer_confidence válidas tras fallo OCR.
- [X] T016 Actualizar `app/services/enrichment_job_store.py` para persistir/servir el mismo objeto saneado y transiciones atómicas: «finish y fail solo cambian desde processing vigente», cancelación borra JSON/filas sensibles/candidatos, «processed_units monotónico y <=total_units», «durante processing results_ready=0, resultados devuelve página vacía» y «páginas 1..n con page_size 1–100 y total estable al finalizar»; ordenar por detection_id en imagen y respetar todos los estados terminales.
- [X] T017 Actualizar `app/services/enrichment_worker.py` para comprobar estado/cierre/TTL entre unidades y antes de publicar, emitir registro fallido con identidad por unidad sin crop y progresar sin superar total. Integrar el contexto de `app/services/inference_metrics.py` en worker y `app/services/enrichment_processing.py`: medir trabajo/unidad y atributos/localización/OCR con duración/RSS/resultado/error seguro y cierre incluso en fallo/cancelación/vencimiento. Publicar al completed, no mantener locks durante inferencia ni prometer interrumpir una llamada ya iniciada.
- [X] T018 Coordinar janitor en `app/core/lifespan.py` con `app/services/image_detection_store.py`, `app/services/enrichment_job_store.py` y `app/services/temporary_artifacts.py`: «TTL del job <=TTL fuente y límite de enriquecimiento», «Janitor cada 1 s, eliminación de originales/resultados sin tráfico», margen máximo 2 s, cierre ordenado y lectura/borrado seguros sin prolongar vigencia.

### Cliente tipado y recursos

- [X] T019 [P] Escribir `frontend/tests/services/apiClient.test.ts` y `frontend/tests/hooks/useObjectUrl.test.ts` para AbortSignal, errores, páginas, revocación replace/reset/expiry/unmount y origen seguro. Usar temporizadores controlados para solicitudes bloqueadas de imagen: detección 120 s, creación 15 s, estado/capacidades 10 s, páginas/medios 30 s, abortando al menor plazo restante/TTL y sin reenviar POST ni extender límites a video por defecto.
- [X] T020 Corregir `frontend/src/services/apiTypes.ts` para DTO con bbox anidada, identidad por fuente/detección y metadatos/trabajos reales; reflejar «detection_id>=1, class_id>=0, class_name no vacío, confidence entre 0 y 1», «track_id: null/ausente para imagen estática», «plate.status: read/unreadable/not_detected/failed», texto solo read, bbox_relative 0–1 y page_size 1–100; validar datos de red, sin reemplazar any por casts ciegos.
- [X] T021 Ampliar `frontend/src/services/apiClient.ts` con aborto, original canónico, páginas y errores seguros; aplicar opciones de plazo solo al recorrido de imágenes (detección 120 s, creación 15 s, estado/capacidades 10 s, páginas/medios 30 s), calculadas con reloj monotónico y recortadas por presupuesto/TTL. Verificar origen antes de adjuntar credencial, limpiar timers, conservar firmas/comportamiento de video/conteo y no reenviar POST automáticamente ni poner secretos en URLs.
- [X] T022 Implementar `frontend/src/hooks/useObjectUrl.ts` con recursos por generación y revocación de originales/anotaciones/recortes en replace/reset/expiry/unmount; liberar upload tras obtener canónico, no crear recursos para respuestas descartadas y no añadir persistencia del navegador.

**Checkpoint**: B1/B2/B4/B5 superan sus pruebas específicas y el cliente entiende los contratos; no entregar historias sobre geometría incoherente o ciclo inseguro.

## Phase 3: US1 — Analizar y enriquecer con una sola acción (P1, MVP)

**Goal**: Un clic encadena detección/enriquecimiento y conserva información útil ante fallo.
**Independent Test**: Imagen válida y API determinista: un POST de cada etapa por acción, datos básicos durante espera, vacío sin enriquecimiento y reintento solo de la etapa fallida.

### Pruebas primero

- [X] T023 [P] [US1] Crear matriz de capacidades en `tests/integration/test_enrichment_readiness.py` y `tests/unit/test_enrichment_core.py`; adaptar `tests/conftest.py`, `tests/enrichment_fixtures.py` y `tests/integration/test_enrichment_job_routes.py`: fixture explícita con adaptadores sintéticos realmente inicializados para los casos que esperan 202, y fixture independiente sin modelos que espera 503 enrichment_unavailable. Probar solo atributos, localizador sin lector, placas completas y todo listo; no forzar ready, cargar pesos reales o relajar aserciones; validar propiedad antes de informar errores de creación.
- [X] T024 [P] [US1] Escribir `frontend/tests/features/image-analysis/useImageAnalysis.test.tsx` y `frontend/e2e/image-analysis.flow.spec.ts` para doble clic/StrictMode, vacío, pendiente, parcial, reintento, fallo HTTP, respuesta A tras B/reset, POST ambiguo y >50 resultados. Con temporizadores controlados verificar ciclo automático <=120 s, solicitudes bloqueadas y presupuesto total con respuestas rápidas, menor TTL, interrupted al vencer plazo local y reanudación explícita del mismo job sin rePOST ni restaurar datos vencidos.

### Implementación

- [X] T025 [US1] Implementar B3 en `app/core/lifespan.py`, `app/api/routes/health.py` y `app/domain/schemas.py`: «attributes, plate_localization, plate_ocr: ready/unavailable según adaptador inicializado» y «status=ready solo si detección y todas las ramas están listas; si falta algo, status=not_ready y HTTP503»; capacidades seguras sin rutas/pesos/excepciones, nunca ready por ausencia de configuración.
- [X] T026 [US1] Separar localización/lectura en `app/services/enrichment_processing.py` y creación en `app/services/enrichment_job_service.py`, conservando la instrumentación de T017. Aceptar atributos o localización útiles aunque health sea 503, conservar bbox si OCR falta/falla y devolver 503 enrichment_unavailable si ninguna rama sirve, después de validar fuente/propiedad; conservar modelos/umbrales/reglas OCR y hacer pasar fixtures operativos y negativos separados de T023.
- [X] T027 [US1] Definir `frontend/src/features/image-analysis/types.ts` y `frontend/src/features/image-analysis/imageAnalysisReducer.ts` con idle/selected/detecting/detected/enrichment_submitting/enrichment_queued/enrichment_processing/ready/partial/detection_failed/enrichment_failed/interrupted/expired/invalidated; «Parcial = alguna rama ausente/fallida», selección única y generación por fuente, sin persistir AbortController/timers/URLs.
- [X] T028 [US1] Implementar `frontend/src/features/image-analysis/useImageAnalysis.ts` desde la acción de usuario con guard sincrónico, identidad `(sessionGeneration, request_id)`, medios autenticados y enriquecimiento según enrichment_eligible; descartar respuestas obsoletas y mantener detecciones válidas ante fallo posterior, sin POST en efecto de montaje.
- [X] T029 [US1] Completar `frontend/src/features/image-analysis/useImageAnalysis.ts` con polling secuencial 1200 ms y ciclo automático de máximo 120 s por inicio explícito, acotado por el menor TTL fuente/job/artefactos; cada solicitud usa el menor límite individual/presupuesto restante/TTL. Detener timers/fetch al agotarlo, entrar en interrupted conservando solo datos vigentes y ofrecer reanudar el mismo job mediante acción explícita sin ampliar TTL ni rePOST ambiguo; distinguirlo del vencimiento real que retira evidencia. Recuperar todas las páginas, no solapar consultas y cancelar con cliente anterior IDs tardíos cuando sea posible.
- [X] T030 [P] [US1] Crear `frontend/src/features/image-analysis/ImageUpload.tsx` con JPEG/PNG, previsualización, sustitución, etiquetas accesibles y una acción principal; comunicar límites/rechazos confirmados por servicio y evitar pulsaciones repetidas durante envío, sin inventar límites nuevos.
- [X] T031 [P] [US1] Crear `frontend/src/features/image-analysis/AnalysisProgress.tsx` con etapas/estados vacío, pendiente, éxito, parcial, fallo, cancelación, interrupción y vencimiento; progreso real, región de estado accesible y recuperación sin respuestas técnicas crudas.
- [X] T032 [US1] Integrar `frontend/src/features/image-analysis/ImageWorkspace.tsx` y `frontend/src/App.tsx`, adaptando `frontend/src/components/ImageAnalysisPanel.tsx` y `frontend/src/components/EnrichmentPanel.tsx` para eliminar el enriquecimiento manual duplicado de imagen y conservar video; mostrar anotación/datos básicos durante espera y una incompatibilidad explícita si falta evidencia del contrato nuevo.
- [X] T033 [US1] Ejecutar T023/T024 y registrar en `specs/006-mejoras-frontend/validation.md` conteo de envíos, recuperación, plazos y resultados del MVP parcial de orquestación; una rama ausente no borra detecciones ni deja espera indefinida. No cerrar todavía la aceptación completa de US1: su escenario de selección durante processing depende de T039 y se verifica en T040.

**Checkpoint MVP parcial**: Orquestación utilizable con B1–B5. La aceptación completa de US1 espera selección T039/T040; fichas/recortes completos esperan US3. No marcar US1 ni toda 006 aceptadas en T033.

## Phase 4: US2 — Seleccionar sobre la imagen (P1)

**Goal**: Recuadros pulsables, selección inequívoca y lista equivalente.
**Independent Test**: Escena controlada: hover, clic/toque/Enter/Espacio, misma selección en recuadro/lista y alineación tras redimensionar, incluidas cajas solapadas.

### Pruebas primero

- [X] T034 [P] [US2] Escribir `frontend/tests/utils/imageGeometry.test.ts` para proporciones vertical/horizontal, imagen W×H, bordes, letterboxing, redimensionamiento y geometría inválida; usar invariantes canónicas de T007 sin ampliar hitboxes sobre vecinos.
- [X] T035 [P] [US2] Escribir `frontend/tests/features/image-analysis/selection.test.tsx` y `frontend/e2e/image-analysis.selection.spec.ts` para hover/foco/selección, teclado/toque, cajas pequeñas/solapadas, foco estable y etiquetas reales. Incluir explícitamente US1 escenario 2: seleccionar un vehículo mientras el enriquecimiento sigue processing y consultar sus datos básicos con atributos/placa pendientes.

### Implementación

- [X] T036 [US2] Implementar proyección en `frontend/src/utils/imageGeometry.ts` desde coordenadas canónicas: left=x_min/W, top=y_min/H y tamaños relativos; descontar márgenes si contain usa caja fija, mantener proporción y rechazar geometría inválida sin estimarla.
- [X] T037 [US2] Crear `frontend/src/features/image-analysis/AnnotatedImageViewer.tsx` con imagen anotada y botones sobre su área real, cursor/énfasis hover, foco visible, selección distinta, nombre accesible, aria-pressed y aria-controls; otros actores siguen visibles y las imágenes estáticas usan «Detección N».
- [X] T038 [P] [US2] Crear `frontend/src/features/image-analysis/DetectionList.tsx` con controles equivalentes siempre disponibles >=44x44, identificador/clase y selección por props; cada vehículo debe poder elegirse aunque su recuadro sea diminuto o esté detrás de otro.
- [X] T039 [US2] Conectar visor/lista y selectedDetectionId en `frontend/src/features/image-analysis/ImageWorkspace.tsx` y `frontend/src/features/image-analysis/imageAnalysisReducer.ts`; identidad por fuente, una selección, foco estable ante nuevos resultados y cierre sin pérdida de contexto.
- [X] T040 [US2] Después de T039, ejecutar `frontend/e2e/image-analysis.selection.spec.ts` y cerrar en `specs/006-mejoras-frontend/validation.md` el escenario pendiente de US1 de selección durante processing, junto con alineación/identidad 360/768/1440 y teclado/toque; no derivar Track ID de detection_id. Este checkpoint completa la aceptación de US1 con US2; la ficha enriquecida completa sigue siendo US3.

**Checkpoint**: Selección verificada con fixtures e integración US1. T040 cierra el escenario de US1 durante processing después de T039; este orden no exige la ficha enriquecida completa de US3.

## Phase 5: US3 — Ficha enriquecida y recortes (P1)

**Goal**: Atributos y evidencia fiel del vehículo/placa correctos, con estados independientes.
**Independent Test**: Seleccionar entre vehículos con resultados desordenados/paginados y estados de placa distintos; comparar crops con regiones conocidas y confirmar que no se inventan datos.

### Pruebas primero

- [X] T041 [P] [US3] Añadir `frontend/tests/utils/evidenceCrop.test.ts` para píxeles/regiones conocidas, vehículo al borde, placa relativa al crop, truncado/clamp, bbox ausente/degenerada, EXIF ya normalizado, canónico inaccesible y liberación de recursos; no usar anotación ni evidencia ajena.
- [X] T042 [P] [US3] Añadir `frontend/tests/features/image-analysis/VehicleDetails.test.tsx` y `frontend/e2e/image-analysis.details.spec.ts`: atributos/confianzas, placa read/unreadable/not_detected/failed, localización válida con OCR fallido, texto canario no read, más de 50 resultados y enriquecimiento sin correspondencia rechazado.

### Implementación

- [X] T043 [US3] Ampliar `frontend/src/utils/imageGeometry.ts` con extracción fiel: vehículo semiabierto y placa «0–1, orden estricto entre extremos; normalizado respecto al crop vehicular canónico, nunca la imagen completa»; canvas solo para píxeles, sin reconstrucción/mejora, con fallo seguro de generación de Blob.
- [X] T044 [US3] Crear `frontend/src/features/image-analysis/EvidenceCrop.tsx` para «tipo vehicle/plate, identidad compuesta, caja válida y URL temporal»; generar solo para selección activa y revocar al cambiar/expirar/desmontar; proporción/alternativa textual y estado explícito ante evidencia ausente.
- [X] T045 [US3] Crear `frontend/src/features/image-analysis/VehicleDetails.tsx` con identificador/clase/confianza, atributos/confianzas y estados independientes; texto solo read autorizado, crop ilegible si localizado y secciones pendientes/fallidas sin ocultar datos válidos ni imprimir JSON.
- [X] T046 [US3] Implementar `frontend/src/features/image-analysis/vehicleView.ts`: «detección, estado de enriquecimiento, atributos, placa y referencias de evidencia. No contiene HTML ni respuestas crudas; error_code se traduce por catálogo seguro»; unir por fuente/detection_id, no posición ni vehicle_key aislado; rechazar resultados sin correspondencia/geometría fiable.
- [X] T047 [US3] Integrar ficha/vista/crops en `frontend/src/features/image-analysis/ImageWorkspace.tsx`, con canónico de US1 y selección US2; secciones pendientes durante processing y datos al completed sin salto de foco, panel en flujo lateral/debajo y sin modal obligatorio.
- [X] T048 [US3] Ejecutar `frontend/e2e/image-analysis.details.spec.ts` y pruebas de crops/ficha; registrar en `specs/006-mejoras-frontend/validation.md` identidad correcta en al menos 20 vehículos sintéticos, placas ilegibles con crop y ausencia de imágenes/texto estimados.

**Checkpoint**: Ficha y crops verificados con datos controlados; lectura real del modelo se evalúa aparte en T067.

## Phase 6: US4 — Presentación profesional, responsive y accesible (P2)

**Goal**: Interfaz formal sin gradientes y con controles/estados claros.
**Independent Test**: Recorrido en 360/768/1440, texto 200%, teclado/toque y movimiento reducido; revisar contraste y estados.

### Pruebas primero

- [X] T049 [P] [US4] Crear `frontend/e2e/image-analysis.visual.spec.ts` con capturas sintéticas reproducibles en tres viewports para inicial, carga, detección, enriquecimiento, éxito, parcial, vacío, fallo, cancelación/interrupción y vencimiento; no aprobar automáticamente referencias visuales recién creadas.
- [X] T050 [P] [US4] Crear `frontend/e2e/image-analysis.accessibility.spec.ts` para nombres/orden de foco, Enter/Espacio/toque, anuncio sin robo de foco, texto 200%, ausencia de scroll horizontal global, movimiento reducido y controles >=44x44; medir contraste de estilos computados sin afirmar conformidad WCAG completa.

### Implementación

- [X] T051 [US4] Definir paleta sólida/tokens mínimos en `frontend/src/styles.css` y scope en `frontend/src/features/image-analysis/image-analysis.css`: gris claro, blanco, texto azul oscuro, acento azul, espaciado 8/16/24/32, sin gradientes ni selectores que alteren LineEditor u otros paneles.
- [X] T052 [US4] Implementar `frontend/src/features/image-analysis/image-analysis.css` con escena predominante/ficha aproximada 340 px en escritorio, una columna en tablet/móvil, controles que envuelven y sin alturas que trunquen; conservar proporción/selección en 360/768/1440 y texto 200%.
- [X] T053 [US4] Completar accesibilidad en `frontend/src/features/image-analysis/ImageUpload.tsx`, `frontend/src/features/image-analysis/AnalysisProgress.tsx`, `frontend/src/features/image-analysis/AnnotatedImageViewer.tsx`, `frontend/src/features/image-analysis/DetectionList.tsx` y `frontend/src/features/image-analysis/VehicleDetails.tsx`; texto >=4.5:1, foco/controles >=3:1, indicadores adicionales al color, objetivos principales 44x44, orden/nombres consistentes y movimiento reducido.
- [X] T054 [US4] Añadir catálogo seguro en `frontend/src/features/image-analysis/imageAnalysisMessages.ts` e integrarlo con `frontend/src/features/image-analysis/AnalysisProgress.tsx` y `frontend/src/features/image-analysis/VehicleDetails.tsx`; traducir validación/autorización/indisponibilidad/vencimiento con siguiente acción y sin secretos, rutas o cuerpos crudos.
- [X] T055 [US4] Revisar las capturas de `frontend/e2e/image-analysis.visual.spec.ts` en el mismo navegador/entorno y registrar revisión/correcciones en `specs/006-mejoras-frontend/validation.md`; inspeccionar legibilidad, cajas, etiquetas y estados antes de aceptar las referencias visuales.
- [X] T056 [US4] Ejecutar `frontend/e2e/image-analysis.accessibility.spec.ts` y completar inspección de contraste/foco/texto ampliado en `specs/006-mejoras-frontend/validation.md`; verificar todos los tamaños y corregir controles inaccesibles/truncados, sin certificar accesibilidad completa solo mediante snapshots.

**Checkpoint**: Recorrido legible/operable con evidencia visual y de accesibilidad, sin cambio funcional del diseño de video.

## Phase 7: US5 — Conservar capacidades y privacidad de sesión (P2)

**Goal**: Mantener imagen/video/conteo y limpiar todos los estados/recursos de sesión.
**Independent Test**: Recorridos previos controlados y reset/cambio de credencial con trabajos activos; limpieza inmediata incluso si falla cancelación, sin restauración por respuesta tardía.

### Pruebas primero

- [X] T057 [P] [US5] Escribir `frontend/tests/sessionLifecycle.test.tsx` y `frontend/e2e/session-lifecycle.spec.ts` para reset/cambio de base/credencial, POST aún sin ID, respuesta tardía, cancelación fallida, recursos vencidos y ausencia de imágenes/placas/credenciales en localStorage/sessionStorage/IndexedDB/logs; no exigir cancelación garantizada al cerrar navegador.
- [X] T058 [P] [US5] Extender `tests/e2e/test_image_and_video_regression.py`, `tests/e2e/test_line_counting_regression.py` y `tests/integration/test_cors.py`, y añadir `frontend/e2e/video-count-regression.spec.ts`; conservar un video activo, estado/anotación, línea/conteos y enriquecimiento de video con sus contratos actuales.

### Implementación

- [X] T059 [US5] Crear `frontend/src/hooks/useSessionLifecycle.ts` con generación común y registro de canceladores/recursos; invalidar/limpiar inmediatamente e intentar cancelaciones de video/conteo/enriquecimiento con el cliente anterior mediante Promise.allSettled, sin esperar confirmación ni guardar datos sensibles en almacenamiento persistente.
- [X] T060 [US5] Conectar el ciclo en `frontend/src/App.tsx`, `frontend/src/components/SessionConfig.tsx` y `frontend/src/features/image-analysis/ImageWorkspace.tsx`; remontar/reset por generación los estados internos y restaurar valores de sesión, incluida la base inicial al reiniciar según 005, sin permitir que respuestas antiguas repongan archivos, IDs o placas.
- [X] T061 [US5] Adaptar `frontend/src/components/VideoJobPanel.tsx`, `frontend/src/components/CountJobPanel.tsx` y `frontend/src/components/EnrichmentPanel.tsx` al registro común; detener timers terminales/expiry/unmount y revocar previews manteniendo controles, contratos y diseño funcional de video/conteo.
- [X] T062 [US5] Aplicar mínimo efectivo fuente/job/artefactos en `frontend/src/features/image-analysis/useImageAnalysis.ts` y `frontend/src/hooks/useSessionLifecycle.ts` para retirar evidencia al vencer y ante 404/410 o pérdida de acceso; no renovar TTL por interacción ni afirmar revocación física de bytes ya recibidos.
- [X] T063 [US5] Ejecutar T057/T058 con el backend de pruebas real y registrar en `specs/006-mejoras-frontend/validation.md` regresión de imagen/video/conteo y reset/cancelación durante procesamiento, sin publicación tardía ni bloqueo de vista.
- [X] T064 [US5] Verificar con `frontend/e2e/session-lifecycle.spec.ts`, `tests/integration/test_enrichment_lifecycle.py` y `specs/006-mejoras-frontend/validation.md` limpieza local inmediata, purga sin tráfico <=2 s y ausencia de datos sensibles fuera de sesión; documentar límites del cierre de navegador/entorno sin presentar best-effort como garantía.

**Checkpoint**: Capacidades previas verificadas y reset común limpia todos los paneles aunque falle cancelación remota.

## Phase 8: Polish & Cross-Cutting Concerns — cierre con evidencia

- [X] T065 [P] Actualizar `README.md` y `specs/006-mejoras-frontend/quickstart.md` con comandos/archivos implementados, original protegido, disponibilidad parcial y prerrequisitos privados; mantener coherentes `specs/006-mejoras-frontend/contracts/backend-additions.md` y `specs/006-mejoras-frontend/contracts/openapi-additions.yaml`, sin cambiar significado de especificaciones históricas ni incluir secretos.
- [X] T066 Ejecutar build/suites pertinentes completas (`npm run build`, `npm run test`, `npm run test:e2e` en `frontend/`; `uv run pytest` en raíz) y registrar versiones/comandos/resultados/bloqueos en `specs/006-mejoras-frontend/validation.md`; resolver regresiones y no declarar exitosas pruebas omitidas o sin recursos.
- [ ] T067 Validar modelos reales y registrar en `specs/006-mejoras-frontend/validation.md` al menos 10 imágenes/20 vehículos, una imagen y video completos, calidad y latencias de validación/inferencia/anotación/total y ramas de enriquecimiento frente a línea base bajo mismo hardware/modelo/parámetros/concurrencia; incluir RSS inicial/final/máximo muestreado, métricas por cuadro de video, eventos seguros de éxito/fallo y ausencia de retención creciente tras procesamiento/limpieza. Verificar ficha <1 s y purga <=2 s; no cambiar pesos/umbrales ni sustituir evidencia real por fixtures.
- [ ] T068 Realizar evaluación SC-007 y registrar resultados anónimos en `specs/006-mejoras-frontend/usability.md`: 5 participantes, al menos 4 completan análisis/consulta sin ayuda en <=2 minutos de interacción activa y al menos 4 califican claridad/presentación >=4/5; sin participantes mantener pendiente, sin inventar respuestas.
- [X] T069 Consolidar en `specs/006-mejoras-frontend/audit.md` trazabilidad FR-001–FR-034 y SC-001–SC-015 con `validation.md`/`usability.md`; distinguir completado/pendiente/bloqueado, preservar DEP-001 de seguimiento real fuera de alcance y comprobar rama feature/006 y ausencia de archivos ajenos incorporados.

## Dependencies & Execution Order

### Orden de fases

```text
Setup T001–T004
  └─ Fundamentos T005–T022
       ├─ US1 T023–T033: MVP parcial de orquestación
       ├─ US2 T034–T040: selección verificable con escena controlada
       └─ US3 T041–T048: ficha verificable con escena/enriquecimiento controlados
US1 + US2 + US3 ──> US4 T049–T056: presentación y accesibilidad
Fundamentos + contratos de sesión de US1 ──> US5 T057–T064
US1 + US2 + US3 + US4 + US5 ──> Cierre T065–T069
```

US2/US3 permiten trabajo y pruebas de componentes aislados con fixtures. Su integración real respeta orquestación T027–T032 -> selección US2 -> ficha US3; US2 no requiere la aceptación completa de US1, que se cierra tras T040. No se afirma independencia de integración donde existe dependencia.

### Dependencias concretas

| Entrega | Depende de |
|---|---|
| T004 servidor de pruebas | T003 |
| T007–T009 B1 | T005; T009 usa T007/T008 |
| T010–T012 B2 | T006 y B1; T012 usa T010/T011 |
| T015–T018 B4/B5 | T013/T014 y fuente B1/B2; T016 usa T015; T017 usa T016; T018 coordina stores/worker corregidos |
| T020–T022 cliente | T019 y contratos B2; T021 usa T020 |
| T025/T026 B3 | T023/fundamentos; T023 migra fixtures operativos/negativos, T026 usa capacidades T025 y conserva instrumentación T017 |
| T027–T032 US1 | T024, cliente y B3; reducer antes del hook, hook antes de integrar; T030/T031 tras definir props |
| T036–T039 US2 | T034/T035; T037 usa T036; T038 puede coincidir con T037; T039 integra ambos con orquestación T027–T032, sin exigir la aceptación completa de US1 |
| T043–T047 US3 | T041/T042 y recursos; T044 usa T043/T022; T047 integra T044/T045/T046 y selección US2 |
| T051–T054 US4 | T049/T050 y componentes US1–US3; CSS compartido secuencial |
| T059–T062 US5 | T057/T058 y contratos de generación; T060 usa T059; T061 después de T060; T062 integra vigencia mínima |
| Validación de cada historia | Su implementación y servidor T004; T033 valida MVP parcial y la aceptación completa US1 requiere T039/T040 |
| Cierre | Todas las historias; T069 usa T066–T068; evaluación externa pendiente impide aceptación completa |

T016/T017/T018/T025 comparten módulos/estado de backend: integrar secuencialmente. App.tsx, ImageWorkspace.tsx, useImageAnalysis.ts, apiTypes.ts y CSS no reciben dos tareas simultáneas.

## Parallel execution examples

Estos ejemplos describen independencia si se reparte trabajo; no ordenan crear agentes.

- **Setup**: T001 Vitest, T002 Playwright y T003 fixtures usan archivos distintos; T004 espera fixtures.
- **Fundamentos**: T005/T006 son suites distintas, igual T013/T014; T019 se escribe sin editar stores una vez definidos contratos.
- **US1**: T023 backend y T024 frontend pueden escribirse en paralelo; después de T027, T030/T031 producen componentes distintos. T028/T029 se editan por turnos.
- **US2**: T034/T035 pruebas independientes; con geometría/props listas, T037 visor y T038 lista usan archivos distintos; T039 integra.
- **US3**: T041/T042 pruebas independientes; tras modelos/helper, T044 crop, T045 ficha y T046 vista se reparten solo sin editar tipos compartidos; T047 integra.
- **US4**: T049 visual y T050 accesibilidad son suites distintas; T051/T052 comparten CSS y no coinciden.
- **US5**: T057 frontend y T058 regresión backend/video pueden escribirse en paralelo; T059–T062 integran sesión secuencialmente.
- **Cierre**: T065 documentación puede coincidir con ejecución; los resultados de T066/T067/T068 se integran por turnos en validation.md.

## Trazabilidad de backend y requisitos

| Paquete del plan | Tareas/comprobaciones |
|---|---|
| B1 Geometría | T005, T007–T009, T034/T036, T041/T043, T067 |
| Observabilidad constitucional | T005, T009, T017, T026, T067 |
| B2 Evidencia/elegibilidad | T006, T010–T012, T020–T022, T028, T044, T062 |
| B3 Disponibilidad | T023, T025/T026, T031/T033 |
| B4 Resultados | T013, T015–T017, T026, T042/T046, T048 |
| B5 Ciclo de vida | T014, T016–T018, T022, T028/T029, T057–T064 |

| Requisitos | Cobertura principal | Criterios de éxito |
|---|---|---|
| FR-001 | T032, T058, T061/T063/T066 | SC-010 |
| FR-002, FR-003, FR-004, FR-005, FR-006 | T024–T033 | SC-001, SC-008 |
| FR-007, FR-008, FR-009, FR-010 | T034–T040 | SC-002, SC-005 |
| FR-011, FR-013, FR-014, FR-015, FR-016 | T013/T015, T041–T048 | SC-002, SC-003, SC-004, SC-012 |
| FR-012 | T010/T020, T035/T037/T040, T069 | SC-011 |
| FR-017, FR-018, FR-019, FR-020, FR-021 | T049–T056 y T068 | SC-005, SC-006, SC-007 |
| FR-022, FR-023, FR-024 | T014/T016–T018, T022, T057–T064 | SC-009, SC-013 |
| FR-025, FR-026, FR-027 | Límites de todas las fases y T065/T069 | Auditoría, SC-010/SC-011 |
| FR-028, FR-029 | T005–T012, T020/T036/T043 | SC-004, SC-012 |
| FR-030 | T023/T025/T026/T031/T033 | SC-008, SC-014 |
| FR-031, FR-032 | T014, T016–T018, T062–T064 | SC-013 |
| FR-033 | T013/T015/T016/T026, T042/T045, T064 | SC-014 |
| FR-034 | T005/T009/T017/T026/T067 | SC-015 |

## Implementation Strategy

1. Completar setup/fundamentos y sus pruebas antes del recorrido definitivo.
2. Entregar T033 como MVP parcial de orquestación; completar selección T039/T040 antes de aceptar US1. No detener la iteración completa en ese incremento.
3. Añadir US2/US3 con fixtures y luego integración; completar US4/US5 sin rediseñar video.
4. Cerrar con evidencia automatizada, visual, modelos reales y participantes. Recursos privados ausentes mantienen pendientes las tareas afectadas.
5. Ejecutar `$speckit-converge` tras implementación para identificar diferencias reales, sin borrar tareas para aparentar completitud.

## Completion conditions

69 tareas, todas inicialmente pendientes: setup 4, fundamentos 18, US1 11, US2 7, US3 8, US4 8, US5 8 y cierre 5. Cinco historias con pruebas explícitas y dependencias de integración declaradas; US1 completa requiere selección US2. Esta fase genera tareas y métricas; no implementa código ni ejecuta pruebas de producto.


## Estado de implementación (2026-11-20)

67 de 69 tareas cerradas con evidencia en validation.md y audit.md. T067 conserva evidencia parcial con modelos reales (6 imágenes/16 vehículos enriquecidos); faltan conjunto y comparación completos. T068 requiere participantes. No se declara aceptación integral mientras sigan abiertas.

Las 69 tareas y sus identificadores se preservan. Las diferencias concretas de representación de estado, proyección y herramientas se explican en implementation-notes.md. No se modificó el checklist de requisitos durante la implementación.


## Estado de ejecución (2026-11-20)

67/69 tareas completadas con evidencia en validation.md y audit.md. Permanecen pendientes T067 (evaluación real comparativa completa; smoke de 6 imágenes y 16 vehículos disponible) y T068 (cinco participantes). No se declara aceptación integral mientras estas comprobaciones estén abiertas.

Las 69 tareas inicialmente pendientes descritas arriba corresponden al estado de generación. Las casillas y esta sección muestran el estado de implementación actual. La equivalencia de estados y las decisiones de geometría están documentadas en implementation-notes.md.


## Phase 9: Convergence

**Fecha**: 2026-11-20. **Resultado**: `tasks_appended`. Revisión del estado presente frente a spec.md, plan.md, las 69 tareas y la constitución; las casillas anteriores no se utilizaron como prueba de cumplimiento. Se revisaron 34 FR, 15 SC (SC-007 como evaluación externa), 26 escenarios de aceptación, 20 decisiones del plan, 5 principios constitucionales y 84 archivos nombrados en las tareas; los 84 existen.

**Resumen**: 13 hallazgos: 3 CRITICAL, 6 HIGH y 4 MEDIUM; 2 missing, 6 partial, 5 contradicts y 0 unrequested. Las prioridades CRITICAL derivan de obligaciones constitucionales de protección de datos y disponibilidad de la API. La revisión no ejecutó de nuevo las suites ni cambió código; se hicieron comprobaciones puntuales en memoria sin almacenar evidencia sensible. Se preservan T001–T069, sus casillas y todas las secciones anteriores.

**Pendientes existentes**: T067 sigue requiriendo evaluación real comparativa con medios/referencia suficientes y T068 requiere participantes. No se duplican esas evaluaciones externas. T081/T082 cierran comprobaciones implementables que faltan aunque los medios reales o participantes todavía no estén disponibles; no sustituyen T067/T068. DEP-001 continúa fuera del alcance y no autoriza seguimiento ficticio.

- [X] T070 **CRITICAL — F01** Retirar inmediatamente la evidencia afectada ante rechazo de acceso en `frontend/src/services/apiClient.ts` y `frontend/src/features/image-analysis/useImageAnalysis.ts`: conservar los estados HTTP 401/404/410 aunque el cuerpo de error se bloquee o agote su plazo; procesar el rechazo de cada descarga sin esperar a `Promise.allSettled` de las demás, abortar solicitudes relacionadas y limpiar URLs/datos/selección con un mensaje de acceso o vencimiento correcto. Evidencia: un 401 con cuerpo suspendido termina como `status=0/request_timeout`; si original queda pendiente y anotación rechaza 401, la fuente sigue visible hasta terminar original. Añadir pruebas de ambos órdenes de respuesta, cuerpo bloqueado, retirada inmediata y ninguna restauración tardía en `frontend/tests/services/apiDeadlines.test.ts` y `frontend/tests/features/image-analysis/lifecycle.test.tsx`. Según Constitución III, FR-024, US5/AC4 y T062 (contradicts).

- [X] T071 **CRITICAL — F02** Completar la purga de originales y anotaciones después de reiniciar el proceso en `app/services/source_artifacts.py`, `app/services/image_detection_store.py`, `app/services/temporary_artifacts.py` y `app/core/lifespan.py`: recuperar o retirar de forma acotada los archivos propios cuya metadata temporal se perdió, sin ampliar TTL, exponer rutas ni borrar archivos ajenos o evidencia vigente recuperable. Evidencia: los constructores conservan archivos existentes, los registros de imagen/anotación arrancan vacíos y el janitor solo recorre esos registros; un archivo de una ejecución interrumpida deja de tener camino de expiración. Probar con dos instancias sucesivas sobre directorios sintéticos, sin llamar al cierre de la primera, más purga sin tráfico y aislamiento de archivos ajenos en `tests/integration/test_enrichment_lifecycle.py`; no prometer eliminación mientras el servicio esté detenido. Según Constitución III, FR-032, SC-013 y T011/T018 (partial).

- [X] T072 **CRITICAL — F03** Sacar la decodificación, orientación, conversión RGB y compresión PNG síncronas del bucle de eventos de la ruta de imagen, conservando validación de bytes/píxeles y la única normalización canónica, en `app/services/image_validation.py` y `app/api/routes/detections.py`. Evidencia: `validate` es async pero ejecuta Pillow/`clean.save` directamente; una comprobación en memoria con imagen sintética 2000×1500 retrasó un heartbeat de 1 ms hasta 37.81 ms, observación puntual y no benchmark. Añadir prueba determinista con barrera de normalización que permita atender health/cancelación mientras se procesa una imagen, sin pesos ni sleeps largos; conservar pruebas EXIF, límites y contrato. Según Constitución V, plan: evitar bloqueos innecesarios de API y T008/T009 (contradicts).

- [X] T073 **HIGH — F04** Completar invalidación de solicitudes y evidencia de video/conteo/enriquecimiento de video en `frontend/src/hooks/useLegacyJob.ts`, `frontend/src/hooks/useSessionLifecycle.ts`, `frontend/src/services/apiClient.ts` y los tres paneles existentes: admitir señales opcionales compatibles, abortar fetch/consumo activo al reset/cambio de identidad/desmontaje/vencimiento y retirar preview/IDs/resultados también ante 401/404/410. Evidencia: los métodos legacy no reciben señales, el hook solo marca `alive=false`, el catch de polling no invoca retirada de preview y la descarga de video fallida solo cambia un mensaje. Mantener cancelación remota con el cliente anterior, tratar ID tardío sin reponer sesión y no aplicar indiscriminadamente los plazos de imagen a video. Cubrir requests suspendidos, cancelación remota fallida, cuerpos tardíos y revocación en `frontend/tests/hooks/useLegacyJob.test.tsx`, `frontend/tests/sessionLifecycle.test.tsx` y `frontend/e2e/session-lifecycle.spec.ts`. Según FR-023/024, US5/AC2–4, plan: invalidación por generación y T059–T064 (partial).

- [X] T074 **HIGH — F05** Separar el estado de cada intento explícito de enriquecimiento en `frontend/src/features/image-analysis/useImageAnalysis.ts`: después de un terminal, descartar el ID/progreso/estado del intento anterior antes de crear el siguiente; si la creación tiene resultado ambiguo, explicarlo sin ofrecer reanudar el ID anterior ni repetir POST automáticamente. Evidencia reproducida en memoria: primer job failed → reintento de creación con timeout conserva `jobId=old-job` y deja `phase=interrupted`; `resume` consulta ese trabajo fallido en lugar de representar la creación desconocida. Añadir pruebas de fallo/cancelación terminal seguidos de creación fallida, timeout o aceptación tardía, conservando detección y TTL sin nuevo POST de imagen. Según FR-005/006/021, US1/AC3/5, plan: recuperación de creación ambigua y T028/T029 (contradicts).

- [X] T075 **HIGH — F06** Modelar carga, éxito y fallo independientes de original/anotación en `frontend/src/features/image-analysis/imageAnalysisReducer.ts`, `useImageAnalysis.ts`, `AnnotatedImageViewer.tsx` e `ImageWorkspace.tsx`; terminar el placeholder al fallar, ofrecer recuperación explícita del medio sin repetir inferencias y conservar los datos/evidencia válidos de la otra descarga. Evidencia: el hook solo publica una advertencia conjunta y el visor interpreta toda URL vacía como “Cargando imagen anotada…”, incluso después de timeout/503/bytes no decodificables; un fallo de anotación también produce un aviso sobre recortes aunque el original haya cargado. Añadir pruebas de fallo independiente, decodificación del img, recuperación y reset durante descarga; los rechazos de acceso siguen T070. Según FR-004/005/026, SC-008, US1/AC3 y T024/T031/T033 (partial).

- [X] T076 **HIGH — F07** Informar en `frontend/src/features/image-analysis/ImageUpload.tsx` los límites reales aplicables de bytes y píxeles/resolución del servicio configurado mediante un mecanismo aditivo compatible, documentado y validado; reutilizar los valores existentes de Settings sin cambiarlos ni fijar límites inventados en el cliente. Evidencia: la carga solo informa “JPEG o PNG · Evidencia temporal y privada”; el catálogo de errores tampoco comunica los valores efectivos y no hay obtención de esos límites. Probar configuración de límites distintos y contexto de rechazo/recuperación, preservando controles del servidor y sin exponer configuración privada. Según FR-002, US4/AC1/5 y T030/T054 (missing).

- [X] T077 **HIGH — F08** Mantener una única línea de conteo por fuente activa en `frontend/src/components/LineEditor.tsx` y `frontend/src/App.tsx`: publicar la eliminación al padre, invalidar la línea al borrar/cambiar video y reiniciar puntos/arrastre cuando cambie la fuente. Evidencia: “Borrar línea” solo ejecuta `setPoints([])`; App conserva `line` para CountJobPanel. Al cambiar preview, App borra su línea pero LineEditor no se remonta ni reacciona a `videoUrl`, por lo que puede seguir dibujando puntos anteriores. Probar que borrar impide POST de conteo hasta definir otra línea y que reemplazar video no conserva trazos/configuración de la fuente previa, sin rediseñar este flujo ni modificar su contrato backend. Según FR-001/023, US5/AC1/2 y T058/T060/T061 (contradicts).

- [X] T078 **MEDIUM — F09** Garantizar foco y contornos distinguibles del visor sobre regiones claras y oscuras en `frontend/src/features/image-analysis/image-analysis.css` y `AnnotatedImageViewer.tsx`, sin tapar evidencia ni ampliar hitboxes; medir el control real en `frontend/e2e/image-analysis.accessibility.spec.ts`. Evidencia: foco/hover blancos, borde normal #91b7ff y selección #ffda74 tienen contra blanco contrastes de 1:1, 2.02:1 y 1.35:1, respectivamente; la prueba actual compara un azul fijo contra blanco sin inspeccionar el foco del overlay. Incorporar escenas de fondo blanco/oscuro, foco visible, selección/hover distintos y alternativa de lista; ejecutar toque real y caja pequeña/solapada en los proyectos táctiles. Según FR-008/009/019, US2/AC1/2/4, SC-005/006 y T035/T050/T053/T056 (partial).

- [X] T079 **MEDIUM — F10** Presentar explícitamente envío, cola y procesamiento en `frontend/src/features/image-analysis/AnalysisProgress.tsx` a partir de `enrichmentStage`, con textos/anuncios distintos y progreso únicamente recibido del servidor, sin mover el foco. Evidencia: el hook guarda submitting/queued/processing, pero el título siempre usa `labels[state.phase]` y el mensaje permanece “Consultando atributos y placas…”, de modo que queued y processing no se diferencian visualmente. Probar cola prolongada, transición a processing y ambos estados con progreso cero. Según FR-004, US1/AC1 y T027/T031 (partial).

- [X] T080 **MEDIUM — F11** Reflejar cancelación/vencimiento en las métricas de unidad de `app/services/enrichment_worker.py`, enlazando el contexto de unidad con las salidas cooperativas, sin cambiar publicación de resultados ni estado de una rama de inferencia que sí terminó. Evidencia reproducida en memoria: cancelación antes de invocar processor emite `enrichment_unit=completed` y `enrichment_job=cancelled`. Ampliar `tests/unit/test_inference_observability.py` y las pruebas del worker con cancelación/TTL antes de inferir y entre evidencias, verificando duración, RSS, correlación y resultado seguros. Según FR-034, plan: observabilidad por trabajo/unidad y T005/T017 (contradicts).

- [X] T081 **HIGH — F12** Completar aceptación integrada de identidad y evidencia con fixtures sintéticos distinguibles en `frontend/e2e/image-analysis.details.spec.ts`, `image-analysis.selection.spec.ts` y sus fixtures: al menos 10 escenas/20 vehículos, más de 50 resultados en varias páginas, orden alterado, detecciones no consecutivas y estados read/unreadable/not_detected/failed. Evidencia: las pruebas de navegador solo recorren dos vehículos y comparan un píxel del primer crop vehicular; 55 resultados se verifican en un hook con cajas iguales, sin probar su asociación visual ni píxeles de placa. Verificar selección/ficha/crop correctos por identidad de fuente/detección, regiones vehiculares y placa relativa, rechazo sin correspondencia y ausencia de texto canario; registrar evidencia sin presentarla como calidad de modelos reales ni cerrar T067 por fixtures. Según FR-013–015, US3/AC1–5, SC-002/004/012 y T035/T041/T042/T048 (partial).

- [X] T082 **MEDIUM — F13** Añadir medición reproducible de aparición de la ficha con datos ya cargados en `frontend/e2e/image-analysis.details.spec.ts`, usando reloj monotónico y un punto final observable de la ficha correcta, separando espera de inferencia/descarga inicial y verificando <1 s en el dispositivo/viewport de evaluación. Evidencia: las aserciones actuales esperan visibilidad con el timeout general de Playwright y no registran duración de interacción; validation.md mantiene SC-003 sin medición. Documentar condiciones y resultados reales en validation.md/audit.md y conservar pendiente cualquier medición que no se ejecute; no sustituir el estudio con participantes. Según SC-003, plan: performance goals y la parte implementable de T067 (missing).

**Orden de implementación**: T070–T072 primero. T073 antecede la regresión completa de sesión y T077; T074/T075/T079 comparten hook/estado y se editan secuencialmente. T078 y T081/T082 completan sus pruebas después de corregir comportamiento; T080 se valida también con las pruebas del worker de B5. Reejecutar suites pertinentes y actualizar audit.md/validation.md durante la siguiente implementación; esta convergencia solo añade esta sección.


## Estado tras corregir convergencia (2026-11-20)

T070–T082 completadas con evidencia en [convergence-validation.md](convergence-validation.md). Estado actual: 80/82 tareas completadas; T067 y T068 permanecen pendientes. No se modificaron sus casillas ni se sustituyeron evaluaciones reales por fixtures. La fase 9 conserva los hallazgos originales como historial de la corrección.


## Phase 10: Convergence

**Revision posterior a T070–T082**: verificacion acotada en el checkout principal, conservando `feature/006-mejoras-frontend` y los cambios existentes. Se revisaron 13 tareas, 17 requisitos funcionales, 8 criterios de exito, 17 escenarios de aceptacion, 9 decisiones del plan y los 5 principios constitucionales aplicables. Las correcciones de T070–T079 y T081–T082 no presentan nuevos pendientes en esta revision. T080 corrige las salidas cooperativas por unidad, pero queda un caso de finalizacion del trabajo descrito en T083. Las casillas y cierres anteriores se conservan como historial; esta seccion actualiza su limite de verificacion.

**Hallazgos nuevos**: 1 partial, severidad MEDIUM; 0 missing, 0 contradicts y 0 unrequested. No se detectaron hallazgos nuevos CRITICAL/HIGH. No se duplican T067 (comparacion real completa), T068 (participantes) ni DEP-001.

- [X] T083 **MEDIUM — F14** Registrar el desenlace real de la publicacion final en las metricas del trabajo de enriquecimiento de `app/services/enrichment_worker.py` y `app/services/enrichment_job_store.py`: obtener o confirmar el resultado de la finalizacion atomica para que `enrichment_job` no registre `completed` si cancelacion o TTL impidieron guardar el resultado entre el ultimo `_continue(job)` y `finish(...)`, o durante la comprobacion final del TTL. Conservar `completed` en unidades/ramas cuya inferencia si termino, la prohibicion de publicar despues de cancelacion/vencimiento, la correlacion y la ausencia de datos sensibles. Evidencia reproducida con SQLite real temporal y un punto de intercalacion antes de `finish`: tanto cancelacion como vencimiento dejan cero unidades publicadas, `enrichment_unit=completed` correcto y `enrichment_job=completed` incorrecto; el worker no recibe ni comprueba el desenlace del store (worker:117–120; store:95–109). Anadir pruebas deterministas de ambos desenlaces en `tests/unit/test_worker_unit_metrics.py` o `tests/unit/test_enrichment_worker_cancellation.py`, incluyendo TTL que vence en la publicacion final; comprobar tambien exito normal, duracion/RSS/correlacion y que ninguna representacion sensible reaparece. Actualizar los informes de validacion/cierre al implementar. Segun FR-034, plan: observabilidad por trabajo/unidad y T017/T080 (partial).

**Evidencia de esta revision**:

- Backend: `.venv/Scripts/python.exe -m pytest -p no:cacheprovider --disable-warnings` con `PYTHONDONTWRITEBYTECODE=1`: 160 pasaron, 2 avisos de dependencias, 23.01 s.
- Frontend: `npm --prefix frontend run test -- --no-cache`: 52 pasaron en 19 archivos.
- TypeScript: `tsc --noEmit --incremental false`, desde frontend: correcto, sin emitir archivos.
- Navegador: Playwright completo con reportes/capturas en el directorio temporal, sin reescribir evidencia versionada: 93 pasaron, 0 omitidos, 0 inesperados, 0 flaky, 122.16 s; escritorio, tablet y movil.
- Sonda adicional sin cambios de codigo: cancelacion/vencimiento intercalados antes de `finish`, usando store SQLite temporal real. Ambos casos reproducen F14; la suite existente no cubre ese punto de carrera.
- Se preservo byte por byte el contenido previo de `tasks.md` antes de este anexo (SHA256 B16192D725A2FDEC2E449E02147E7E6008523E2194479F91657B26BEC3DA69C9).

**Resultado**: `tasks_appended`; una tarea nueva en fase 10. Estado actual: 80/83 tareas marcadas, con T067, T068 y T083 pendientes. Ejecutar `$speckit-implement SPECIFY_FEATURE_DIRECTORY=specs/006-mejoras-frontend` para T083 y repetir converge despues. No se declara aceptacion integral de la iteracion.

## Cierre de T083 (2026-11-20)

T083 completada. `finish` devuelve el desenlace decidido bajo el bloqueo de publicación; el worker lo utiliza para cerrar la métrica del trabajo. Se preservan métricas completed de unidades/ramas ya terminadas y la prohibición de publicar tras cancelación/vencimiento. Seis escenarios deterministas nuevos reproducen cancelación, TTL antes/durante escritura, éxito y limpieza posterior sin reescribir el desenlace confirmado. Antes de corregir fallaron cuatro; después pasan los seis.

Validación: 29 pruebas focalizadas; suite backend completa 166 aprobadas (2 avisos de dependencias, 22.70 s); frontend 52 aprobadas; navegador integrado imagen/video/conteo 9 aprobadas en tres viewports (39.80 s). Ver [convergence-validation.md](convergence-validation.md).

Estado vigente: **81/83 tareas completadas**. Solo T067 y T068 siguen pendientes; no se declara aceptación integral de la iteración. La fase 10 anterior conserva el hallazgo y los resultados previos como historial.
