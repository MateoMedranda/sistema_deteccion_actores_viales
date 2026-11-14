# Tasks: Interfaz web prototipo vial

**Input**: Documentos de diseño en specs/005-interfaz-web-prototipo-vial/

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/frontend-backend.md y quickstart.md.

**Tests**: Obligatorios. Las pruebas unitarias, de componentes, de contrato, integración y E2E se implementan antes de la funcionalidad correspondiente y deben verificarse primero en fallo.

**Organization**: Las tareas están agrupadas por historia de usuario para permitir una entrega y validación independientes.

## Format: [ID] [P?] [Story] Description

- **[P]**: Puede ejecutarse en paralelo porque modifica archivos diferentes y no depende de otra tarea incompleta.
- **[Story]**: Relación con la historia de usuario.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Crear el proyecto React/Vite y sus herramientas de pruebas sin modificar todavía el comportamiento del backend.

- [ ] T001 Crear el esqueleto React + Vite + TypeScript y scripts de desarrollo, compilación y pruebas en frontend/package.json, frontend/vite.config.ts, frontend/tsconfig.json, frontend/index.html y frontend/src/main.tsx
- [ ] T002 Configurar Vitest, React Testing Library, jsdom y la estructura de pruebas en frontend/vitest.config.ts, frontend/src/test/setup.ts y frontend/tests/
- [ ] T003 [P] Configurar Playwright y una API simulada reproducible para recorridos sin pesos de modelos en frontend/playwright.config.ts y frontend/tests/e2e/
- [ ] T004 [P] Excluir artefactos de Node, reportes, videos de Playwright y valores de entorno del frontend en frontend/.gitignore y .gitignore
- [ ] T005 [P] Documentar comandos Node/npm y los prerrequisitos locales de frontend en README.md y specs/005-interfaz-web-prototipo-vial/quickstart.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Preparar compatibilidad segura del backend, contratos tipados y estado de sesión antes de construir paneles de usuario.

**⚠️ CRITICAL**: No iniciar historias de usuario hasta terminar esta fase.

### Tests de compatibilidad del backend

- [ ] T006 [P] Crear pruebas de integración de preflight y orígenes CORS permitidos/rechazados, incluida X-API-Key y la prohibición de comodín, en tests/integration/test_cors.py
- [ ] T007 [P] Ampliar pruebas de integración para DELETE de conteo propio, ajeno, terminal y no existente en tests/integration/test_count_job_routes.py
- [ ] T008 [P] Ampliar pruebas de contrato para DELETE /api/v1/count-jobs/{countJobId} y respuestas seguras en tests/contract/test_count_jobs_contract.py

### Implementación de compatibilidad del backend

- [ ] T009 Añadir la configuración tipada FRONTEND_ALLOWED_ORIGINS con valores locales explícitos y validación sin comodín para rutas protegidas en app/core/config.py y .env.example
- [ ] T010 Configurar middleware CORS a partir de FRONTEND_ALLOWED_ORIGINS, permitiendo OPTIONS y X-API-Key sin revelar secretos, en app/main.py
- [ ] T011 Implementar cancelación idempotente, aislada por propietario y segura de trabajos de conteo en app/services/count_job_service.py y app/services/count_job_store.py
- [ ] T012 Exponer DELETE /api/v1/count-jobs/{countJobId} con estados HTTP coherentes en app/api/routes/count_jobs.py y actualizar la documentación OpenAPI resultante en specs/005-interfaz-web-prototipo-vial/contracts/frontend-backend.md

### Núcleo compartido del frontend

- [ ] T013 [P] Crear tipos TypeScript para respuestas, estados terminales, errores seguros, medios protegidos, trabajos y puntos normalizados en frontend/src/services/apiTypes.ts
- [ ] T014 [P] Crear validación de URL HTTP(S), normalización sin barra final y prueba unitaria de entradas inválidas en frontend/src/utils/urlValidation.ts y frontend/tests/unit/urlValidation.test.ts
- [ ] T015 [P] Crear traductor de errores {code, message, request_id} a mensajes de UI sin cuerpos crudos, rutas, cabeceras ni API key, con pruebas en frontend/src/services/errorMapping.ts y frontend/tests/unit/errorMapping.test.ts
- [ ] T016 Implementar ApiClient base que use URL y API key en memoria, FormData, AbortController y resolución de URL relativa de artefacto en frontend/src/services/apiClient.ts
- [ ] T017 Crear pruebas unitarias del ApiClient para X-API-Key, FormData, URL relativa y ausencia de secretos en URL/localStorage en frontend/tests/unit/apiClient.test.ts
- [ ] T018 Implementar DemoSessionProvider con los campos apiBaseUrl, apiKey, activeImage, activeVideo, activeCount, activeEnrichment y limpieza de estado solo en memoria en frontend/src/state/demoSession.tsx
- [ ] T019 Implementar hook para descargar artefactos autenticados como Blob y revocar URL.createObjectURL al reemplazar, limpiar o desmontar en frontend/src/hooks/useObjectUrl.ts
- [ ] T020 Crear pruebas unitarias de revocación de Blob y de que los medios no se cargan con una URL remota directa en frontend/tests/unit/useObjectUrl.test.ts
- [ ] T021 Implementar polling secuencial con setTimeout, AbortController y detención por estados terminales, 404, 409, 410, reinicio o desmontaje en frontend/src/hooks/usePolling.ts
- [ ] T022 Crear pruebas unitarias de polling sin solicitudes superpuestas y cancelación por estado terminal en frontend/tests/unit/usePolling.test.ts
- [ ] T023 Implementar configuración de sesión, entrada de API key, URL de backend, reinicio y componente de estado/error seguro en frontend/src/components/SessionConfig.tsx, frontend/src/components/SafeStatus.tsx y frontend/src/App.tsx
- [ ] T024 Crear prueba de componente para configuración temporal, reinicio y ausencia de API key en la vista/almacenamiento del navegador en frontend/tests/component/SessionConfig.test.tsx

**Checkpoint**: CORS y DELETE de conteo son verificables; el frontend tiene sesión efímera, cliente seguro, descarga protegida, polling y estructura de aplicación.

---

## Phase 3: User Story 1 - Analizar una imagen vial (Priority: P1) 🎯 MVP

**Goal**: Permitir cargar una imagen, recibir detecciones y visualizar una imagen anotada protegida.

**Independent Test**: Con backend simulado y una API key válida, la persona configura sesión, selecciona imagen, ve estado y detecciones con imagen anotada; archivo inválido o error remoto muestran un mensaje seguro.

### Tests for User Story 1

- [ ] T025 [P] [US1] Crear pruebas del método de análisis de imagen, descarga autenticada de imagen anotada y mapeo de errores en frontend/tests/unit/imageApi.test.ts
- [ ] T026 [P] [US1] Crear pruebas de componente para carga, progreso, resultado anotado, cajas/clase/confianza y archivo inválido en frontend/tests/component/ImageAnalysisPanel.test.tsx

### Implementation for User Story 1

- [ ] T027 [US1] Añadir al ApiClient la operación POST /api/v1/detections/images y GET autenticado de imagen anotada en frontend/src/services/apiClient.ts
- [ ] T028 [US1] Implementar ImageAnalysisPanel con selección de archivo, progreso visible, detecciones y Blob anotado en frontend/src/components/ImageAnalysisPanel.tsx
- [ ] T029 [US1] Integrar ImageAnalysisPanel con DemoSessionProvider y navegación principal en frontend/src/App.tsx y frontend/src/state/demoSession.tsx
- [ ] T030 [US1] Ejecutar la prueba independiente de imagen y documentar el resultado esperado de SC-001 en frontend/tests/component/ImageAnalysisPanel.test.tsx y specs/005-interfaz-web-prototipo-vial/quickstart.md

**Checkpoint**: US1 funciona de extremo a extremo como MVP sin requerir video, conteo ni enriquecimiento.

---

## Phase 4: User Story 2 - Procesar y explorar un video (Priority: P1)

**Goal**: Cargar un video único, seguir su trabajo y explorar artefacto anotado, resumen y detecciones temporales.

**Independent Test**: Con una respuesta simulada de 202 y transiciones queued/processing/completed, la interfaz conserva un único job_id, consulta sin solapamiento y muestra video anotado, resumen y detecciones paginadas; un terminal fallido/cancelado/vencido se comunica de forma segura.

### Tests for User Story 2

- [ ] T031 [P] [US2] Crear pruebas del ApiClient para crear, consultar, cancelar, paginar detecciones, consultar resumen y descargar video anotado en frontend/tests/unit/videoApi.test.ts
- [ ] T032 [P] [US2] Crear pruebas de componente para progreso, estados terminales, paginación, un solo video activo y Blob de video en frontend/tests/component/VideoJobPanel.test.tsx

### Implementation for User Story 2

- [ ] T033 [US2] Añadir operaciones de trabajos de video y artefactos protegidos al ApiClient en frontend/src/services/apiClient.ts
- [ ] T034 [US2] Implementar VideoJobPanel con carga, polling, cancelación, resumen, detecciones paginadas y video anotado Blob en frontend/src/components/VideoJobPanel.tsx
- [ ] T035 [US2] Impedir iniciar un segundo video mientras exista uno activo y permitir reiniciar/cancelar según FR-003 en frontend/src/state/demoSession.tsx y frontend/src/components/VideoJobPanel.tsx
- [ ] T036 [US2] Integrar el panel de video y su limpieza con App y DemoSessionProvider en frontend/src/App.tsx y frontend/src/state/demoSession.tsx

**Checkpoint**: US2 permite demostrar procesamiento de un video y explorar sus resultados de forma independiente.

---

## Phase 5: User Story 3 - Configurar y observar conteo por línea (Priority: P1)

**Goal**: Dibujar una línea normalizada sobre el video terminado, iniciar conteo y observar eventos/totales por clase y sentido.

**Independent Test**: Sobre un video terminado simulado, el usuario dibuja dos puntos no coincidentes, redimensiona la vista sin cambiar sus coordenadas normalizadas, inicia conteo y ve estado, eventos y resumen; reiniciar intenta DELETE y limpia sin esperar la respuesta.

### Tests for User Story 3

- [ ] T037 [P] [US3] Crear pruebas unitarias de conversión viewport↔normalizado, rango [0,1], redimensionamiento y rechazo de línea de longitud cero en frontend/tests/unit/lineCoordinates.test.ts
- [ ] T038 [P] [US3] Crear pruebas del ApiClient para crear, consultar, cancelar y consultar eventos/artefacto del conteo en frontend/tests/unit/countApi.test.ts
- [ ] T039 [P] [US3] Crear pruebas de componente de dibujo, ajuste, borrado, conteo y actualización de eventos/totales en frontend/tests/component/LineEditor.test.tsx y frontend/tests/component/CountJobPanel.test.tsx

### Implementation for User Story 3

- [ ] T040 [US3] Implementar utilidades de coordenadas normalizadas y validación de distancia no nula en frontend/src/utils/lineCoordinates.ts
- [ ] T041 [US3] Añadir operaciones de conteo y DELETE de conteo al ApiClient en frontend/src/services/apiClient.ts
- [ ] T042 [US3] Implementar LineEditor SVG con dos puntos, arrastre, borrado y ResizeObserver en frontend/src/components/LineEditor.tsx
- [ ] T043 [US3] Implementar CountJobPanel con creación, polling, eventos paginados, totales por clase/sentido y video Blob anotado en frontend/src/components/CountJobPanel.tsx
- [ ] T044 [US3] Integrar conteo con el video terminado y la limpieza/cancelación segura de sesión en frontend/src/App.tsx y frontend/src/state/demoSession.tsx

**Checkpoint**: US3 permite configurar y validar conteos por línea sin coordenadas manuales.

---

## Phase 6: User Story 4 - Consultar atributos y placas protegidos (Priority: P2)

**Goal**: Solicitar enriquecimiento de una imagen o video vigente y mostrar atributos y placa según autorización del backend.

**Independent Test**: Con resultados simulados de imagen y video, la interfaz muestra atributos, estados read/unreadable/not_detected/failed y texto únicamente para read; un reinicio elimina el texto de placa y resultados.

### Tests for User Story 4

- [ ] T045 [P] [US4] Crear pruebas del ApiClient para crear, consultar, cancelar y paginar resultados de enriquecimiento en frontend/tests/unit/enrichmentApi.test.ts
- [ ] T046 [P] [US4] Crear pruebas de componente para fuente vigente, progreso, estados de placa, texto autorizado y limpieza al reiniciar en frontend/tests/component/EnrichmentPanel.test.tsx

### Implementation for User Story 4

- [ ] T047 [US4] Añadir operaciones de enriquecimiento y resultados paginados al ApiClient en frontend/src/services/apiClient.ts
- [ ] T048 [US4] Implementar EnrichmentPanel con selección de fuente vigente, polling, atributos, paginación y estados seguros de placa en frontend/src/components/EnrichmentPanel.tsx
- [ ] T049 [US4] Mostrar plate.text solamente cuando plate.status sea read y eliminar texto/resultado ante reinicio, cierre, vencimiento o error en frontend/src/components/EnrichmentPanel.tsx y frontend/src/state/demoSession.tsx
- [ ] T050 [US4] Integrar enriquecimiento de imagen/video con App y DemoSessionProvider en frontend/src/App.tsx y frontend/src/state/demoSession.tsx

**Checkpoint**: US4 demuestra atributos y placas sin persistencia ni exposición de texto no autorizado.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Verificar la experiencia completa, seguridad, compilación, documentación y evidencia de entrega.

- [ ] T051 [P] Añadir recorrido Playwright de imagen, video, línea/conteo, enriquecimiento, reinicio y estados de error con API simulada en frontend/tests/e2e/prototype-vial.spec.ts
- [ ] T052 [P] Añadir prueba de que la API key, texto de placa, URLs Blob e IDs se limpian al reiniciar/desmontar en frontend/tests/component/sessionCleanup.test.tsx
- [ ] T053 [P] Añadir pruebas de accesibilidad básica de etiquetas, foco y mensajes de estado en frontend/tests/component/accessibility.test.tsx
- [ ] T054 Ejecutar npm run test, npm run test:e2e y npm run build; corregir errores de tipado, pruebas y construcción en frontend/
- [ ] T055 Ejecutar uv run pytest tests/contract/test_count_jobs_contract.py tests/integration/test_count_job_routes.py tests/integration/test_cors.py y registrar resultados en specs/005-interfaz-web-prototipo-vial/audit.md
- [ ] T056 Actualizar instrucciones de instalación, URL configurable, CORS, límites conocidos y demostración de flujos en README.md y specs/005-interfaz-web-prototipo-vial/quickstart.md
- [ ] T057 Revisar que no existan API keys, rutas privadas, texto de placa no autorizado, localStorage/sessionStorage ni CORS comodín en frontend/ y app/, y registrar el resultado en specs/005-interfaz-web-prototipo-vial/audit.md
- [ ] T058 Ejecutar la guía completa de quickstart, verificar SC-001 a SC-006 y completar evidencia de auditoría en specs/005-interfaz-web-prototipo-vial/audit.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no depende de trabajo anterior.
- **Foundational (Phase 2)**: depende de Setup y bloquea todas las historias.
- **US1 (Phase 3)**: depende de Foundational y es el MVP.
- **US2 (Phase 4)**: depende de Foundational; usa la sesión y cliente comunes.
- **US3 (Phase 5)**: depende de Foundational y requiere un video terminado de US2 para la demostración integrada.
- **US4 (Phase 6)**: depende de Foundational y puede probarse con fuente simulada; se integra después de US1/US2.
- **Polish (Phase 7)**: depende de las historias que se entreguen.

### User Story Dependencies

- **US1**: independiente después de Phase 2.
- **US2**: independiente después de Phase 2; comparte infraestructura, no implementación de US1.
- **US3**: usa VideoJob de US2 como fuente para el flujo real.
- **US4**: usa fuentes de US1 o US2, pero su cliente y panel se prueban con fixtures independientes.

### Parallel Opportunities

- T003, T004 y T005 pueden ejecutarse tras T001.
- T006, T007, T008, T013, T014 y T015 pueden ejecutarse en paralelo al inicio de Phase 2.
- Las tareas de prueba marcadas [P] de cada historia pueden implementarse en paralelo.
- US1, US2 y US4 pueden distribuirse tras Phase 2; US3 requiere la integración de video terminada.

## Parallel Example: User Story 3

```text
T037: pruebas de coordenadas en frontend/tests/unit/lineCoordinates.test.ts
T038: pruebas del contrato de conteo en frontend/tests/unit/countApi.test.ts
T039: pruebas de componentes en frontend/tests/component/LineEditor.test.tsx y frontend/tests/component/CountJobPanel.test.tsx
```

## Implementation Strategy

### MVP First

1. Completar Phase 1 y Phase 2.
2. Completar US1 (T025–T030).
3. Verificar análisis de imagen y SC-001 antes de avanzar.

### Incremental Delivery

1. Añadir US2 para demostrar video asíncrono.
2. Añadir US3 para la línea de conteo visual.
3. Añadir US4 para atributos y placas protegidos.
4. Ejecutar Phase 7 para evidencia, seguridad y guía final.

