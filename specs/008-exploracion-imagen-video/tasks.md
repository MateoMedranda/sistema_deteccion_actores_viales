# Tasks: Exploración de imágenes y video

**Feature**: `008-exploracion-imagen-video` · **Rama**: `feature/008-exploracion-imagen-video` · **Fecha**: 2026-11-21.

**Input**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contratos](contracts/backend-additions.md), [gateway](contracts/gateway.md), [UI](contracts/frontend-interactions.md), [schemas](contracts/schemas.json), [ejemplos](contracts/examples.json), [protocolo](validation-protocol.md) y [quickstart](quickstart.md). Constitución: `.specify/memory/constitution.md`.

**Estado**: backlog de implementación; ninguna casilla implica código entregado. Esta etapa genera tareas y línea base PTS, sin modificar producto ni ejecutar inferencias.

**Tests**: requeridos por FR-028 y principio IV. Escribir/ejecutar primero los casos nuevos en rojo, implementar y pasar a verde; usar pruebas existentes como guardas. No escribir pruebas que solo repitan el algoritmo candidato como oráculo.

**Organización**: historias por prioridad P1 (US1, US2, US4, US5), después P2 (US3, US6); se conserva la numeración de la spec. Setup/foundation preceden al producto; cierre reúne aceptación.

## Formato y reglas de ejecución

- `- [ ] Tnnn [P?] [USn?] descripción con rutas`. [P] indica oportunidades locales con archivos distintos y dependencias satisfechas; no autoriza agentes automáticamente ni paralelismo entre tareas dependientes.
- Rutas relativas a la raíz del checkout principal. Archivos nuevos son destinos futuros; no abrir otro worktree ni cambiar de rama. Conservar configuración, índice y cambios existentes; ningún `git add .`, reset, clean o checkout destructivo.
- Dependencias indicadas por ID son prerrequisitos del producto de cada tarea. El orden de las fases es la ruta recomendada; las pruebas de una historia se completan antes de su implementación correspondiente.
- Commits al cerrar cada incremento y la implementación, con archivos propios explícitos. Esta generación tendrá su commit de documentación; no ejecutar implementación o publicación durante tasks.
- No cambiar detector, tracker, pesos, clases, umbrales, política OCR o autenticación; backend solo recibe las adiciones previstas. No nuevos crops de video, historial, fuentes en vivo ni selección de contornos sobre video pausado.
- Un gate no ejecutado/fallido deja su tarea y criterio abiertos. Se puede continuar trabajo independiente y documentación de pendientes sin fingir el PASS ni bloquear su registro. Los cierres de incremento registran estado real; no equivalen a aceptación integral.

## Fase 1: Setup — baseline y material controlado

**Objetivo**: Congelar la referencia y preparar la validación sin cambiar el producto.

**Prueba independiente**: Baseline identificada y fixtures separados de006/007, con fuentes y condiciones reproducibles.

### Implementación y verificación

- [X] T001 Registrar baseline, rama feature/008, versiones/dispositivos efectivos, límites vigentes y cambios previos; conservar pendientes006/T067–T068 y007/T061–T064/T070. Fijar el renderer anterior y su huella antes de modificarlo, sin activar un selector público o cambiar modelos/umbrales. Rutas: `specs/008-exploracion-imagen-video/validation.md`, `tests/fixtures/video_presentation/legacy_renderer.py`. Dependencias: ninguna. Trazabilidad: FR-026, FR-027, SC-009.
- [X] T002 [P] Crear generador de fixtures sintéticos propios: «10 escenas de imagen,3 densas», «>=6 clips con2 densos>=21actores» y «>=3 tramos continuos>=120cuadros». Guardar manifiesto versionado, raw y trayectorias de referencia conocidas, ajuste/reserva separados y cuadros fijados antes de medir. No copiar medios privados ni sobrescribir fixtures007. Rutas: `tests/e2e/build_video_presentation_fixtures.py`, `frontend/e2e/fixtures/video-presentation/manifest.json`. Dependencias: T001. Trazabilidad: SC-003, SC-004, SC-005.
- [X] T003 [P] Ejecutar y registrar las guardas existentes de imagen/video/conteo/enriquecimiento/autorización y muestras golden antes de cambios. Añadir únicamente los contadores/contratos de compatibilidad008 necesarios para detectar alteraciones de raw, API previa y política OCR; ningún fixture equivale a precisión OCR real. Rutas: `tests/contract/test_008_legacy_compatibility.py`, `specs/008-exploracion-imagen-video/validation.md`. Dependencias: T001. Trazabilidad: FR-026, FR-028, SC-009.

**Checkpoint**: Registrar evidencia y pendientes; no alterar el alcance de las historias.

## Fase 2: Foundational — arnés compartido

**Objetivo**: Preparar clocks, barreras, propietarios y transportes inyectables usados por todas las historias.

**Prueba independiente**: Los arneses quedan aislados de runtime privado y no inician inferencias reales ni dependen de fixtures sobrescritos.

### Implementación y verificación

- [X] T004 [P] Preparar helpers de backend con dos propietarios, reloj/TTL, barreras de codificación/publicación, fake upstream streaming y contadores de modelos/colas. Usar directorios temporales y fábricas inyectadas; el arnés de gateway no importa app.main global ni inicia su lifespan. Rutas: `tests/fixtures_008.py`, `tests/conftest.py`. Dependencias: T002, T003.
- [X] T005 [P] Preparar escenarios de navegación, sesión administrada, fases de video, recibo incierto, páginas y medios retrasados; configurar arnés008 separado que permita primero mock directo y después gateway real con upstream inyectado. Puertos4173/4174/8767 solo de pruebas, sin reutilizar servidores personales ni alterar la suite existente. Rutas: `frontend/tests/fixtures/workspaces008.ts`, `frontend/e2e/managed-scenarios.ts`, `frontend/playwright.008.config.ts`, `tests/e2e/serve_managed_test_api.py`. Dependencias: T002, T003.

**Checkpoint**: Registrar evidencia y pendientes; no alterar el alcance de las historias.

## Fase 3: US1 — Navegación Imagen/Video (P1, MVP)

**Objetivo**: Dos espacios accesibles con estado vigente conservado al navegar.

**Prueba independiente**: Imagen/Video por teclado y toque en360/768/1440 y200%, sin cancelar/duplicar jobs, con retirada de evidencia oculta al vencer.

### Pruebas primero

- [X] T006 [P] [US1] Escribir primero regresiones de tabs y persistencia: «activeMode(image|video). Inicial image»; dos paneles montados, foco/aria, generación estable y navegación sin POST/cancel. Comprobar que ocultar Video pausa y conserva currentTime y que TTL sigue activo oculto; ejecutar en rojo antes de implementar. Rutas: `frontend/tests/components/WorkspaceTabs.test.tsx`, `frontend/tests/features/workspacesLifecycle.test.tsx`. Dependencias: T004, T005. Trazabilidad: FR-001, FR-002, FR-024.
- [X] T007 [P] [US1] Escribir primero el recorrido de tabs con procesos en curso y evidencia vencida, teclado/toque y texto200% en los tres tamaños; utilizar el modo de sesión previo/mock mientras US2 no exista. Acreditar respuestas por epoch/generation y controles>=44px; ejecutar en rojo. Rutas: `frontend/e2e/workspace-navigation.spec.ts`. Dependencias: T004, T005. Trazabilidad: FR-003, SC-001.
### Implementación y verificación

- [X] T008 [P] [US1] Crear WorkspaceTabs con tablist/tab/tabpanel, aria-selected, relación de IDs y roving tabindex; flechas/Home/End recorren, Enter/Espacio activa. No cambiar key, generación o jobs al navegar; si el panel oculto tenía foco, devolverlo al tab activo. Rutas: `frontend/src/components/WorkspaceTabs.tsx`. Dependencias: T006, T007.
- [X] T009 [P] [US1] Crear VideoWorkspace inicial que compone VideoJobPanel, EnrichmentPanel, LineEditor y CountJobPanel vigentes bajo identidad de fuente, conservando acciones existentes hasta US5. Mantenerlo montado/hidden y pausar solo reproducción al ocultarlo; no crear todavía otra orquestación de enriquecimiento. Rutas: `frontend/src/features/video-analysis/VideoWorkspace.tsx`. Dependencias: T006, T007.
- [X] T010 [US1] Integrar ambos workspaces en App bajo sessionEpoch estable: «Una imagen y un video por sesión, sin historial ni localStorage de medios/resultados/secretos». Navegar solo actualiza modo; cambiar identidad/reset sí limpia ambos. Conservar temporalmente configuración previa para que US1 sea comprobable antes de US2. Rutas: `frontend/src/App.tsx`. Dependencias: T008, T009. Trazabilidad: FR-001, FR-002.
- [X] T011 [US1] Ajustar cabecera y distribución de modos con colores sólidos, min-width:0, panel oculto fuera del recorrido y controles>=44×44; validar360/768/1440 y200% sin scroll horizontal global ni acciones recortadas. Rutas: `frontend/src/styles.css`. Dependencias: T010. Trazabilidad: FR-003.
- [X] T012 [US1] Pasar pruebas de US1 y registrar capturas/retención/TTL; confirmar el incremento de navegación con sus archivos pertinentes. No declarar cumplida configuración por entorno, zoom o video nuevo hasta sus historias. Rutas: `specs/008-exploracion-imagen-video/validation.md`. Dependencias: T011. Trazabilidad: SC-001, SC-009.

**Checkpoint**: US1 se valida con su prueba independiente antes de dar por entregado el incremento.

## Fase 4: US2 — Configuración administrada y gateway seguro (P1)

**Objetivo**: Retirar la introducción manual de URL/key del flujo habitual y conservar autorización sin publicar la credencial.

**Prueba independiente**: Bootstrap válido/ausente/inválido/rechazado, ingreso local/privado, canario ausente, streaming/Range y cliente anterior compatibles.

### Pruebas primero

- [ ] T013 [P] [US2] Escribir primero guardas de configuración/sesión: un principal por instancia, loopback o ingreso privado autenticado existente, cookie/CSRF/Origin/Host, bootstrap/reset/cupo/TTL y canarios. «Origin/CORS/cookie emitida a cualquier visitante no sustituyen esa frontera». Probar que crear gateway no importa app.main/lifespan/modelos; ejecutar en rojo. Rutas: `tests/unit/test_web_sessions.py`, `tests/integration/test_web_gateway_security.py`. Dependencias: T004, T005. Trazabilidad: FR-004, FR-005, FR-007, SC-002.
- [ ] T014 [P] [US2] Escribir primero ataques y recursos del relay: allowlist exacta, traversal/doble escape/query/redirect/destino ajeno, límite chunked, autenticación antes de cuerpo, cortes de stream/deadline y cierre real de cupos; Range200/206/416 y TTL con medio pausado. No usar Origin como autenticación. Rutas: `tests/integration/test_web_gateway_proxy.py`, `tests/integration/test_web_gateway_media.py`. Dependencias: T004, T005. Trazabilidad: FR-006, FR-024.
- [ ] T015 [P] [US2] Escribir primero contrato de GET /api/v1/web-policy protegido: ImagePolicy/VideoPolicy/Capabilities de schemas.json,401/503/no-store, límites vigentes y cero Settings/rutas/secretos;200 autorizado admite capacidades false. Añadir prueba de parsers de bootstrap/transporte sin cambiar el cliente directo. Rutas: `tests/contract/test_web_policy.py`, `frontend/tests/services/managedTransport.test.ts`. Dependencias: T004, T005. Trazabilidad: FR-004, FR-006.
### Implementación y verificación

- [ ] T016 [US2] Crear WebSettings y ejemplo privado de entorno: WEB_BACKEND_URL «Origen http(s) fijo, sin usuario/clave/query/fragmento/path distinto de /; HTTPS salvo loopback. No procede del navegador.»; WEB_BACKEND_API_KEY «SecretStr no vacío, no placeholder; una credencial/principal por instancia. No serializar Settings.»; WEB_ORIGIN exacto sin wildcard/Host coincidente, WEB_STATIC_DIR=frontend/dist sin exponer .env/fuentes. Mantener secrets fuera de VITE_*. Permitir solo .env.web.example ficticio en gitignore; HTTPX pasa a runtime con el rango existente, sin upgrades. Reglas literales adicionales: WEB_ORIGIN «Origen público exacto sin wildcard; http solo loopback, https para remoto. Host debe corresponder.»; WEB_STATIC_DIR «frontend/dist por defecto; no exponer otros directorios, .env o archivos fuente.» Rutas: `app/web/settings.py`, `.env.web.example`, `.gitignore`, `pyproject.toml`. Dependencias: T013.
- [ ] T017 [P] [US2] Añadir modelos de política/capacidades conforme a schemas.json y WebPolicyService; exponer GET protegido delegando en el servicio e incluir router en app.main. image/video conservan media_types y límites actuales; capacidades son booleanos no sensibles. No cambiar require_api_key, owners ni CORS/orígenes previos. Rutas: `app/domain/schemas.py`, `app/services/web_policy_service.py`, `app/api/routes/web_policy.py`, `app/main.py`. Dependencias: T015.
- [ ] T018 [P] [US2] Implementar RAM sessions: «hash de session_id aleatorio256bits, csrf_token aleatorio256bits, epoch UUID, created_at/expires_at UTC»; «900 predeterminado; permitido60..3600; absoluto, no renovado por solicitudes.» y «128 predeterminado;1..1024. Capacidad agotada429, no expulsar una sesión activa para admitir otra.» Sin medios/owner elegido por visitante; cookie host-only/Path=/HttpOnly/Strict/Secure en HTTPS, excepción HTTP solo loopback; cleanup<=2s y cierre borra RAM. Incluir «revisión de credencial configurada y hasta2 intenciones activas/corrientes»; la cookie contiene solo identificador opaco. Rutas: `app/web/sessions.py`. Dependencias: T016, T013.
- [ ] T019 [US2] Implementar relay cerrado según tabla completa de contracts/gateway.md, IDs «[A-Za-z0-9][A-Za-z0-9_-]{0,127}», page>=1/page_size1..100 sin duplicados y perfil único007. Rechazar destinos/paths no canónicos; descartar credenciales/identidad/Host/Forwarded del cliente y agregar solo key fija. AsyncClient compartido16 conexiones/8keepalive,16 solicitudes/2uploads,429 sin cola; trust_env=false/TLS/redirects=false. Bloques<=64KiB y límites exactos del contrato. Rutas: `app/web/proxy.py`. Dependencias: T016, T018, T014.
- [ ] T020 [US2] Completar cierre y presupuestos del relay en el mismo módulo: JSON entrada16KiB/salida2MiB; multipart límite backend+64KiB, imagen64MiB, placa PNG2MiB/header2048 y MP4stream2GiB. Deadlines120/180/15(sondeo10)/30/10/60s por operación, connect2/pool<=.05/read30, minTTL absoluto. Contar bytes sin Content-Length; finally cierra response/cupo. Accept-Encoding:identity, headers permitidos/no-store, errores seguros, logs httpx/httpcore redactados/WARNING sin URL/cookies/key. Rutas: `app/web/proxy.py`. Dependencias: T019. Trazabilidad: FR-005, FR-006, FR-024.
- [ ] T021 [US2] Añadir excepción nativa solo para los dos MP4 del contrato: cookie válida, Host/Fetch Metadata/CORP same-origin, estado/TTL por GET previo y reautorización del contenido. Range de un intervalo/If-Range,200/206/416; rechazar multi-range y no permitir JSON/mutaciones sin CSRF. Ningún token/key en URL y cierre al vencer/desconectar. Rutas: `app/web/proxy.py`. Dependencias: T020.
- [ ] T022 [US2] Crear app.web.main con lifecycle ligero, guardas de ingreso y StaticFiles solo frontend/dist; POST /web/session consulta política protegida y devuelve WebSession/cookie o503/401 sin key/URL, DELETE conCSRF204 invalida. No CORS abierto ni carga de modelos. Conectar proxy/cleanup; garantizar estado del operador no borrado por reset. Rutas: `app/web/main.py`. Dependencias: T017, T018, T021. Trazabilidad: FR-004, FR-007.
- [ ] T023 [US2] Extender ApiClient/apiTypes con transporte administrado de mismo origen+/web-api, cookie/CSRF y parsers WebSession/WebPolicy. Preservar firmas/camino de clave directa para callers/tests previos, deadlines/AbortSignal/metadatos/401-404-410;403 del gateway retira sesión. Validar URL de artefacto dentro de origen/prefijo y nunca emitir X-API-Key en modo administrado. Rutas: `frontend/src/services/apiClient.ts`, `frontend/src/services/apiTypes.ts`. Dependencias: T022, T015.
- [ ] T024 [US2] Crear useManagedSession y ConnectionStatus para ready/configuration_missing/configuration_invalid/upstream_unavailable/access_rejected; epoch/expiry/CSRF solo memoria. Reset aborta/cancela known jobs best-effort5s antes de DELETE y limpia fuentes de ambos modos sin borrar configuración administrada. Capacidades false no se presentan como key inválida. Rutas: `frontend/src/hooks/useManagedSession.ts`, `frontend/src/components/ConnectionStatus.tsx`. Dependencias: T023.
- [ ] T025 [US2] Integrar sesión administrada en App y eliminar SessionConfig del flujo habitual; configurar proxy de desarrollo /web y /web-api hacia4174 preservando Host/Origin, navegador4173 y backend8000. Producción sirve dist desde gateway; no importar variables secretas en Vite ni exponer gateway públicamente sin ingreso autorizado. Rutas: `frontend/src/App.tsx`, `frontend/vite.config.ts`. Dependencias: T024.
- [ ] T026 [US2] Añadir/ejecutar E2E de sesión real de prueba y canario: build/HTML/config/red/logs con0 apariciones de key, bootstrap fallido seguro, reset/TTL/stream/Range, modos y flujo de imagen007 funcionando por gateway; validar también cliente directo previo y sin acceso anónimo por conocer IDs. Rutas: `frontend/e2e/managed-session.spec.ts`, `specs/008-exploracion-imagen-video/validation.md`. Dependencias: T025. Trazabilidad: SC-002, SC-009.
- [ ] T027 [US2] Registrar despliegue local/privado validado, límites y resultados de US2; confirmar incremento. No declarar protegido un ingreso público sin autenticación existente ni degradar a exponer la API key si falla el gateway. Rutas: `specs/008-exploracion-imagen-video/validation.md`. Dependencias: T026. Trazabilidad: SC-002.

**Checkpoint**: US2 se valida con su prueba independiente antes de dar por entregado el incremento.

## Fase 5: US4 — Video legible, estable y publicación segura (P1)

**Objetivo**: Contornos sin rótulos, paleta007 y suavizado causal solo visual; video final confirmado sin carreras de publicación.

**Prueba independiente**: Sobre6clips, raw/conteo/evidencia intactos, fases reales, cancelación/TTL/encoder sin archivos tardíos; gates de geometría y fluidez medidos, nunca supuestos.

### Pruebas primero

- [ ] T028 [P] [US4] Escribir primero golden/paridad007, RGB->BGR y pruebas del filtro: clase/corte/hueco/ausencia, clamps/degeneradas, redondeo, alphas y fallback; demostrar igualdad de raw/conteo/evidencia antes/después. Registrar ejecución en rojo. Rutas: `tests/unit/test_class_presentation.py`, `tests/unit/test_video_presentation.py`. Dependencias: T004. Trazabilidad: FR-012, FR-013, FR-014.
- [ ] T029 [P] [US4] Escribir primero contratos históricos/nuevos y carreras de EOF/encoding/publishing/finish con cancelación/expiry/reinicio: total estimado erróneo no fuerza cuadros reales; no liberar worker hasta reap; cleanup Windows sin huérfanos ni MP4/raw tardíos. Cubrir migración repetible de históricos con frame_total_confirmed=false no nullable y los13 ejemplos válidos/9inválidos, incluido null explícito rechazado; API anterior puede omitir el flag. Usar barreras, no sleeps frágiles. Rutas: `tests/contract/test_video_job_phases.py`, `tests/integration/test_video_publication_lifecycle.py`. Dependencias: T004. Trazabilidad: FR-015, FR-017, FR-024.
- [ ] T030 [P] [US4] Escribir primero oráculos de jitter residual, lag independiente, IoU, baseline estable/degeneradas y agregación de3pares. Incluir candidato peor, fallo de corrida y RSS FFmpeg para impedir un PASS por omitir muestras o usar velocidad real como jitter. Rutas: `tests/performance/test_video_presentation_evaluator.py`. Dependencias: T002, T004. Trazabilidad: SC-004, SC-005, SC-006.
### Implementación y verificación

- [ ] T031 [US4] Extraer fuente única de007 sin cambiar sus valores: «version1, classes con13 claves y {label,color}; fallback_color=#64748B» y «Clave=class_name.trim().toLowerCase(); desconocida conserva nombre como texto escapado.» Empaquetar JSON para Python, loader tipado y frontend con API anterior; allow de Vite solo al activo, nunca a la raíz privada. No guardar elegibilidad/identidad en paleta. Rutas: `app/domain/class_presentation.json`, `app/services/class_presentation.py`, `frontend/src/features/image-analysis/classPresentation.ts`, `frontend/vite.config.ts`, `pyproject.toml`. Dependencias: T028, T027. Trazabilidad: FR-012, FR-026.
- [ ] T032 [US4] Añadir campos opcionales/históricos de VideoJobAdditions y migración PRAGMA/INSERT explícito: «queued|frames|encoding|publishing|ready|failed|cancelled, o null si histórica/desconocida.»; frame_total_confirmed «bool no nullable; false significa conteo no confirmado, también en históricos; true solo después de EOF real.»; video_metadata «null hasta ready; objeto de salida confirmada descrito abajo.»; eligible_track_count «null antes de ready, luego número de track IDs elegibles distintos según configuración del servidor.»; classes_present «null antes de ready, luego lista única de nombres observados, sin confundir observaciones con vehículos.» Conservar status previo, null solo en los cuatro campos que lo admiten y flag histórico false con NOT NULL DEFAULT 0; API008 incluye siempre booleano, parser legacy normaliza ausencia a false y rechaza null explícito. No fabricar metadata. Rutas: `app/domain/models.py`, `app/domain/schemas.py`, `app/services/video_job_store.py`. Dependencias: T029. Trazabilidad: FR-017.
- [ ] T033 [P] [US4] Implementar PresentedBox efímera: «frame_index/track_id/class, bbox filtrada entera/clamp y profile_id=gated-ema-v1». Mantener únicamente IDs actuales y miniatura gris32×18 previa al dibujo; resets por primer cuadro/hueco/clase/MAD>=.25/IoU<.25/centro>.25diagonal/razón fuera[2/3,1.5]. Candidato «combinación EMA de(cx,cy,w,h) con alphas[.65,.8,.9,1], en ese orden.» Round half-to-even/clamp/IoU>=.90 contra raw visible; último caso raw exacta. Degenerada se registra como inválida; sin observación no extrapolar. No mutar FrameDetection ni adquirir lock de store. Rutas: `app/services/video_presentation.py`. Dependencias: T028, T031. Trazabilidad: FR-013, FR-014, SC-005.
- [ ] T034 [US4] Implementar transiciones y contador real por EOF: «processing_phase=frames/encoding/publishing exige status=processing. ready exige completed, metadatos confirmados y conteo/clases presentes.» Metadata «video_metadata={width,height,fps,frame_count,duration_seconds,timebase:"processed-cfr"}» y «duration=frame_count/fps». No forzar processed_frames al estimado; 100 de cuadros puede anteceder encoding. Calcular elegibles/clases sobre raw según servidor, sin usar summary.detections como vehículos. Rutas: `app/services/video_job_store.py`, `app/services/video_job_service.py`, `app/services/video_worker.py`. Dependencias: T032. Trazabilidad: FR-017, FR-018.
- [ ] T035 [US4] Integrar paleta y filtro solo en representación del VideoProcessor; conservar detector/tracker/clases/thresholds/raw/FrameDetection y geometría usada por evidencia/conteo. Quitar putText de identificadores vehiculares; dibujar trazos de clase y auxiliar blanco/negro, sin glifos. Mantener línea/totales del artefacto003 y todos los cuadros/FPS/tamaño/encoder. Raw conserva «job_id, frame_index0-based, track_id>=1, class_id/name, confidence y bbox half-open entera en el cuadro canónico». Rutas: `app/services/video_processing.py`. Dependencias: T033, T034. Trazabilidad: FR-012, FR-014, FR-015, FR-023, FR-026.
- [ ] T036 [US4] Sustituir ejecución no cooperativa de FFmpeg por supervisor Popen con -nostdin/salida acotada, mismos parámetros H264; sondeo<=50ms, presupuesto=min(60s,deadline vigente restante). Al cancelar/expirar terminate/espera1s/kill/reap efectivo antes de liberar cupo. Cerrar handles en worker y limpiar parciales sin excepciones/paths privados en logs; no aumentar timeout/colas. Rutas: `app/services/video_processing.py`, `app/services/video_worker.py`. Dependencias: T035. Trazabilidad: FR-015, FR-024.
- [ ] T037 [US4] Hacer finish atómico propietario/processing/TTL y asociar MP4+raw solo si sigue autorizado/vigente; devolver desenlace efectivo completed/cancelled/expired/failed y emitir métricas acordes. Cancel/expiry no publican detecciones tardías ni liberan cupo mientras trabajo real siga vivo. Recuperar processing tras reinicio sin reutilizar raw/parciales previos. Rutas: `app/services/video_job_store.py`, `app/services/video_job_service.py`, `app/services/video_worker.py`. Dependencias: T036. Trazabilidad: FR-024, FR-027.
- [ ] T038 [US4] Conectar janitor con eliminación segura de rutas purgadas; no perder referencias al borrar filas. Worker posee archivos/procesos abiertos; servicio reintenta limpieza tras cierre y lifespan coordina shutdown sin bloquear event loop ni borrar desde HTTP un archivo en uso. Comprobar Windows y ausencia de artefactos huérfanos sin ampliar TTL. Rutas: `app/services/video_job_service.py`, `app/services/video_job_store.py`, `app/core/lifespan.py`. Dependencias: T037. Trazabilidad: FR-024, SC-009.
### Pruebas primero

- [ ] T039 [P] [US4] Escribir primero parser/UI para metadata null histórica, fase/estado inválidos, total estimado/confirmado y100% mientras encoding. Probar flag histórico false, ausencia legacy->false, null explícito rechazado, leyenda en escenas mixtas elegibles/no elegibles/desconocidas y aviso general exacto del contrato UI; no afirmar elegibilidad individual ni inferirla de nombre/color. Cubrir classes_present null/vacía y eligible_track_count null/0/>0. Trazado por servidor sin overlay temporal de cliente; ejecutar en rojo. Rutas: `frontend/tests/services/videoPhases.test.ts`, `frontend/tests/features/VideoProgress.test.tsx`. Dependencias: T005. Trazabilidad: FR-012, FR-017.
### Implementación y verificación

- [ ] T040 [US4] Extender parsers/tipos aditivos compatibles de video y crear VideoProgress con fase de procesamiento/encoding/publishing, conteos reales y estado indeterminado cuando corresponde. Conservar null histórico solo en fase/metadata/elegibles/clases; frame_total_confirmed siempre booleano en respuesta008, false histórico/no confirmado, ausencia de API anterior->false y null explícito rechazado. Nunca interpretar progress_percent=100 como MP4 disponible. Preparar región separada para enriquecimiento de US5. Rutas: `frontend/src/services/apiTypes.ts`, `frontend/src/features/video-analysis/VideoProgress.tsx`. Dependencias: T039, T038, T027. Trazabilidad: FR-017.
- [ ] T041 [US4] Integrar progreso y leyenda externa de clases presentes usando catálogo compartido en VideoWorkspace, conservando flujo manual previo hasta US5. Contornos están en MP4, con proporción/pantalla completa; no dibujar números ni una capa clicable temporal. Si classes_present confirmada no vacía, mostrar aviso «El enriquecimiento se aplica a vehículos elegibles según la configuración del servicio; otras detecciones pueden aparecer sin ficha.». Nombre desconocido escapado/fallback y «Clase no reconocida»; null->«Clases todavía no confirmadas», []->«Sin clases detectadas». eligible_track_count=0 indica no aplicable solo para la fuente; null no confirmado. No atribuir elegibilidad por clase, copiar configuración del servidor ni añadir campos API. Rutas: `frontend/src/features/video-analysis/VideoWorkspace.tsx`, `frontend/src/styles.css`. Dependencias: T040, T031. Trazabilidad: FR-012, FR-013.
- [ ] T042 [US4] Implementar evaluador del protocolo con referencias/manifiesto congelados: J_center/J_size como RMS de primeras diferencias residuales, gate por tramo/canal .8 o1e-6 si estable, IoU>=.90 en>=95%, degeneradas como fallo y lag k=-3..3 con soporte común/empate menor|k|/estacionarios no informativos. Separar pruebas raw del coste completo; exportar solo agregados/huellas/condiciones sin medios/OCR/paths privados. Rutas: `scripts/evaluate_video_presentation.py`. Dependencias: T030, T033. Trazabilidad: FR-027, SC-004, SC-005.
- [ ] T043 [US4] Ejecutar unidad/contrato/lifecycle y evaluación controlada de>=6clips/50cuadros prefijados por clip y>=3tramos>=120cuadros; verificar paridad raw, trazos/clases, alineación/cortes/ausencias y gates de fluidez/IoU/lag con resultados reales. Si gated-ema-v1 no supera gate, conservar presentación segura y dejar tarea/SC-005 pendientes, sin ajustar reserva ni inventar ganancia. Rutas: `specs/008-exploracion-imagen-video/validation.md`, `frontend/e2e/video-presentation.spec.ts`. Dependencias: T041, T038, T042. Trazabilidad: SC-004, SC-005, SC-009.
- [ ] T044 [US4] Registrar incremento de presentación y publicación con resultados logrados/pendientes; commit de archivos pertinentes. SC-006 queda reservado a medición completa final: no prometer coste aprobado por pasar tests sintéticos. Rutas: `specs/008-exploracion-imagen-video/validation.md`. Dependencias: T043. Trazabilidad: SC-010.

**Checkpoint**: US4 se valida con su prueba independiente antes de dar por entregado el incremento.

## Fase 6: US5 — Procesamiento y enriquecimiento automáticos (P1)

**Objetivo**: Una acción por video, progreso independiente, reproducción temprana y recuperación acotada sin duplicados.

**Prueba independiente**: Éxito/parcial/cero elegibles/recibo perdido/red/cancelación/TTL con una sola cola por intención, video usable antes del enriquecimiento y conteo previo conservado.

### Pruebas primero

- [ ] T045 [P] [US5] Escribir primero contratos y carreras de POST video/enrichment: dos propietarios, mismo key/fingerprint, conflicto, header ausente/inválido, validación antes de replay, TTL sin renovar y recibo original queued tras completed/fallo. Verificar una fila/cola/inferencia, hash incremental y eliminación solo del staged extra; migración repetida conserva filas históricas. Rutas: `tests/contract/test_job_idempotency.py`, `tests/integration/test_job_idempotency_concurrency.py`. Dependencias: T004. Trazabilidad: FR-016, FR-018, FR-024.
- [ ] T046 [P] [US5] Escribir primero reducer/hook en StrictMode con intención guardada antes de await, recibo202 perdido, GET de estado real, replay misma intención, polling sin solape, navegación oculta, cambio de fuente y eventos tardíos. Cubrir máquinas separadas, reproducción durante enriquecimiento, fallos parciales/cero elegibles y retiro por401/403/404/410; ejecutar en rojo. Rutas: `frontend/tests/features/videoAnalysisReducer.test.ts`, `frontend/tests/features/useVideoAnalysis.test.tsx`. Dependencias: T005. Trazabilidad: FR-016, FR-017, FR-019, FR-020, FR-024.
- [ ] T047 [P] [US5] Escribir primero vínculo X-UI-Intent UUID/HMAC por sesión/operación, último intento conservado incluso tras respuesta, recibo perdido y max2referencias; ausencia permitida para imagen legacy y rechazada con422 web_intent_required en upload/enriquecimiento de video antes de upstream/cola; UUID inválido devuelve422 web_intent_invalid. Verificar Idempotency-Key opcional en API directa como caso distinto. Probar sesión distinta/expirada, reemplazo solo explícito y no exponer clave derivada en navegador/logs. Rutas: `tests/integration/test_web_gateway_intents.py`. Dependencias: T022, T004. Trazabilidad: FR-005, FR-016.
### Implementación y verificación

- [ ] T048 [US5] Migrar ambos stores con «Header opcional Idempotency-Key,16..128 caracteres [A-Za-z0-9_-]»; almacenar SHA256 nullable idempotency_key_hash y request_fingerprint, «UNIQUE parcial(owner_key_id,idempotency_key_hash) por store.» PRAGMA idempotente/INSERT nombrado. Admitir/replay bajo mismo lock/transacción: mismo owner/key/fingerprint recibo original; distinto válido409, sin renovar created_at/expires_at, duplicar cola ni ledger permanente. Legacy null conserva comportamiento. Rutas: `app/services/video_job_store.py`, `app/services/enrichment_job_store.py`, `app/domain/models.py`. Dependencias: T045, T038. Trazabilidad: FR-016, FR-024.
- [ ] T049 [US5] Añadir huella de upload incremental SHA256(MIME normalizado+nulo+bytes), validación/límites existentes antes de replay y autenticación antes de cuerpo. Crear una sola fila/cola y devolver recibo original202; borrar solo copia staged nueva en replay/conflicto/error. No usar nombre/path ni alterar TTL/worker/modelo. Rutas: `app/services/video_job_service.py`, `app/api/routes/video_jobs.py`. Dependencias: T048. Trazabilidad: FR-016, FR-018.
- [ ] T050 [US5] Añadir idempotencia opcional de enriquecimiento sobre JSON canónico source.kind/source_id con guardas de owner/fuente/TTL; replay mismo recibo original202 sin cola/cómputo nuevo. Mantener409fuente no terminada/400no_eligible_vehicles/503capacidades y política/evidencia por track. CORS directo añade solo Idempotency-Key conservando auth/orígenes/métodos. Rutas: `app/services/enrichment_job_service.py`, `app/api/routes/enrichment_jobs.py`, `app/main.py`. Dependencias: T049. Trazabilidad: FR-016, FR-018, FR-019.
- [ ] T051 [US5] Requerir X-UI-Intent UUID para nuevos POST video/enriquecimiento de video; derivar Idempotency-Key con HMAC(secreto efímero,sesión+operación+intención), nunca key aportada del navegador. Sesión conserva hasta2 intenciones corrientes, incluso tras recibir respuesta, hasta reemplazo explícito/TTL; imagen legacy puede omitir intención. Ausencia requerida/UUID inválido=>422 web_intent_required/web_intent_invalid antes de reenviar; Idempotency-Key de API directa sigue opcional. No reenviar fuera de sesión ni renovar vencimientos. Rutas: `app/web/sessions.py`, `app/web/proxy.py`. Dependencias: T050, T047. Trazabilidad: FR-016, FR-024.
- [ ] T052 [P] [US5] Crear máquinas tipadas: «procesamiento: idle/uploading/checking/queued/processing/ready/failed/cancelled/interrupted/expired.»; «medio: idle/loading/available/failed/expired.»; «enriquecimiento: waiting/submitting/queued/processing/completed/not_applicable/failed/cancelled/interrupted/expired.»; «resultados: idle/loading/ready/failed; página actual25 y ficha seleccionada.» Identidades «video: epoch+generation+videoJobId+enrichmentJobId+trackId.» y «conteo: epoch+generation+videoJobId+lineVersion+countJobId.» Guardar intentos/fechas límite sin historia; rechazar todo evento ajeno/antiguo. Rutas: `frontend/src/features/video-analysis/videoAnalysisReducer.ts`. Dependencias: T046. Trazabilidad: FR-017, FR-019, FR-024.
- [ ] T053 [US5] Implementar useVideoAnalysis y soporte ApiClient para intención: bloqueo síncrono antes de await;202 siempre seguido de GET real; polling «sin superposición cada1.2s», timeout10s. Ready vigente+eligible>0 autoencadena una vez;0/400no_eligible->not_applicable. Red->interrupted/Reanudar GET; POST incierto solo reenvío explícito MISMA intención/payload; nuevo intento solo tras fallo/cancelación conocido. Cancelar enrichment conserva video y no reinicia detección. Rutas: `frontend/src/features/video-analysis/useVideoAnalysis.ts`, `frontend/src/services/apiClient.ts`. Dependencias: T052, T051, T040. Trazabilidad: FR-016, FR-018, FR-019, FR-020.
### Pruebas primero

- [ ] T054 [P] [US5] Escribir primero pruebas de reproductor cookie/Range y conteo: pause/seek/fullscreen/hide, error=>GET sin nuevo job, expiry aun pausado, fuentes tardías, retiro de src y geometría del MP4 procesado. No descargar MP4 entero en Blob ni aceptar rutas arbitrarias. Rutas: `frontend/tests/features/VideoPlayer.test.tsx`, `frontend/tests/features/videoCountIdentity.test.tsx`. Dependencias: T005, T053. Trazabilidad: FR-020, FR-023, FR-024.
### Implementación y verificación

- [ ] T055 [US5] Crear VideoPlayer con URL relativa permitida autenticada y reproducción nativa/Range, metadata confirmada y proporción/fullscreen. Ocultar pausa conservando tiempo; minTTL retira src/peticiones aunque pausado. Error de medio consulta estado autorizado para resolver401/404/410 sin inferir o crear jobs; liberar listeners/handles al cambiar epoch/fuente. Rutas: `frontend/src/features/video-analysis/VideoPlayer.tsx`. Dependencias: T054, T053. Trazabilidad: FR-013, FR-020, FR-023, FR-024.
- [ ] T056 [US5] Completar VideoProgress con dos regiones independientes aria-live/progressbar y estados reales; total desconocido/encoding/publishing indeterminados, enriquecimiento por unidades/track reales. Video disponible aparece antes del resultado; éxito con errores se etiqueta parcial, lectura ausente no figura como éxito OCR. Rutas: `frontend/src/features/video-analysis/VideoProgress.tsx`. Dependencias: T053, T055. Trazabilidad: FR-017, FR-019, FR-020.
- [ ] T057 [US5] Sustituir coordinación manual visible por hook/reducer, subida única y acciones de cancelación/reanudación/reintento de etapa; conservar componentes legacy para callers previos sin duplicarlos en pantalla. Integrar LineEditor/CountJobPanel sobre videoJobId/lineVersion y geometría procesada; fuente nueva invalida línea/count/enrichment/selección.401global/403guardas limpia ambos;404/410solo fuente; errores de tratamiento conservan otra evidencia. Rutas: `frontend/src/features/video-analysis/VideoWorkspace.tsx`, `frontend/src/components/LineEditor.tsx`, `frontend/src/components/CountJobPanel.tsx`, `frontend/src/styles.css`. Dependencias: T056. Trazabilidad: FR-016, FR-019, FR-023, FR-024.
- [ ] T058 [US5] Ejecutar E2E con gateway/upstream controlado de espera, frames100+encodinglento, publicación, éxito/parcial/cero elegibles,503, red, aceptación perdida/concurrencia, replay, cancel/TTL y fuente nueva. Contar POST/colas/modelos: una intención no duplica trabajo, video reproduce antes de enrichment, conteo sigue válido y reproducción/seek no infiere. Probar reset con jobs conocidos y fuente independiente. Rutas: `frontend/e2e/video-analysis-flow.spec.ts`, `specs/008-exploracion-imagen-video/validation.md`. Dependencias: T057, T045, T047. Trazabilidad: SC-007, SC-008, SC-009.
- [ ] T059 [US5] Registrar resultados y commit del incremento automático sin certificar fichas/paginación de US6 aún no implementadas; documentar límites/coste de enrichment separado y fallos conocidos con identidad segura. Rutas: `specs/008-exploracion-imagen-video/validation.md`. Dependencias: T058. Trazabilidad: FR-027, SC-007.

**Checkpoint**: US5 se valida con su prueba independiente antes de dar por entregado el incremento.

## Fase 7: US3 — Zoom y recorrido de la escena original (P2)

**Objetivo**: Explorar el original y sus contornos en una única geometría sin alterar selección, recortes o inferencias.

**Prueba independiente**: 10escenas/3densas,50puntos por escena, fit/100/200/400%, error<=1px y p95<=200ms; arrastre no selecciona, teclado/toque equivalentes y0 operaciones nuevas.

### Pruebas primero

- [ ] T060 [P] [US3] Escribir primero tests de escala/ancla/proyección, resize hidden/visible, scroll clamp, fuente nueva, drag>=6px y clic suprimido solo del gesto; pointercancel/blur/foco y teclas dentro de botones. Mantener IDs/crops/selección007 y comprobar cero previewGET/POST adicionales; ejecutar en rojo. Rutas: `frontend/tests/features/SceneViewport.test.tsx`, `frontend/tests/features/sceneViewportGeometry.test.ts`. Dependencias: T005, T012. Trazabilidad: FR-008, FR-009, FR-010, FR-011.
- [ ] T061 [P] [US3] Escribir primero recorrido de zoom/pan/selección en10escenas con3densas y50puntos prefijados por escena. Instrumentar render monotónico y>=30operaciones por viewport para p95 nearest-rank; incluir etiquetas ausentes, focos/targets44px y página sin desborde. No inferir de nuevo para preparar captura. Rutas: `frontend/e2e/scene-viewport.spec.ts`. Dependencias: T005, T002, T012. Trazabilidad: SC-003.
### Implementación y verificación

- [ ] T062 [US3] Crear helpers puros del viewport: «scale finita>0 y<=4» y «anchor normalizado[0,1]²»; «Ajustar=min(1,anchoInterior/W,altoInterior/H)». Intrínseco100%=1px original/CSS; clamp de scroll conserva ancla normalizada, fuente nueva->fit y dimensiones0 ocultas no sobrescriben encuadre. Estado transitorio pointerId/dragOrigin/suppressActivation no se persiste. Campos ligados a «sourceId/generation, naturalWidth/Height, mode(fit|intrinsic)» y scrollLeft/Top. Rutas: `frontend/src/features/image-analysis/sceneViewportGeometry.ts`. Dependencias: T060, T061. Trazabilidad: FR-008, FR-010.
- [ ] T063 [US3] Crear SceneViewport con toolbar Ajustar/100/200/400/Acercar/Alejar/Restablecer, escenario W*scale×H*scale con contornos porcentuales/border-box/trazo CSS constante. «contenedor max-height=min(70vh,720px), min-width:0 y scroll propio». Pointer capture solo al drag>=6px, cleanup cancel/blur, flechas40px/Shift120/Home cuando tiene foco sin interceptar teclas de controles ni zoom global. Touch deja desplazar página en fit y pan local al ampliar. Rutas: `frontend/src/features/image-analysis/SceneViewport.tsx`. Dependencias: T062. Trazabilidad: FR-008, FR-009, FR-011.
- [ ] T064 [US3] Integrar original canónico y contornos en un escenario único; conservar foco>hover>selección, lista equivalente44px, ficha/crops007/identidad y hitboxes. Zoom/pan no modifica datos/TTL ni descarga preview o repite análisis. Evitar scroll horizontal de página y mantener encuadre al alternar workspaces. Rutas: `frontend/src/features/image-analysis/AnnotatedImageViewer.tsx`, `frontend/src/features/image-analysis/ImageWorkspace.tsx`, `frontend/src/features/image-analysis/image-analysis.css`. Dependencias: T063, T027. Trazabilidad: FR-009, FR-010, FR-011, FR-026.
- [ ] T065 [US3] Ejecutar las pruebas/mediciones de zoom en360/768/1440 y texto200%; registrar máximo error<=1px, identidad del100% de selecciones y p95<=200ms con dispositivo/condiciones. Guardar resultados/capturas controladas y commit del incremento; no marcar SC-003 si no se ejecutó o falla un gate. Rutas: `specs/008-exploracion-imagen-video/validation.md`. Dependencias: T064. Trazabilidad: SC-003, SC-009.

**Checkpoint**: US3 se valida con su prueba independiente antes de dar por entregado el incremento.

## Fase 8: US6 — Lista y ficha de enriquecimiento por trayectoria (P2)

**Objetivo**: Consultar todas las páginas con track ID real y evidencia temporal comprensible; revisar propuesta de inspección pausada futura.

**Prueba independiente**: Todos los resultados de>=3páginas accesibles, identidad real y referencia i/fps solo con metadata confirmada; consultar/pausar/buscar produce0inferencias ni llamadas a crops007 de imagen.

### Pruebas primero

- [ ] T066 [P] [US6] Escribir primero parsers/contratos de track_id real, evidence_frame_indexes raíz/placa y evidence_frame_index por atributo; límites/duplicados/negativos/fuera de frame_count, provenance ausente y used_enhancement sin lectura. Conservar todos los resultados paginados y null históricos sin inventar tiempos u origen. Rutas: `frontend/tests/services/videoEvidenceParsing.test.ts`. Dependencias: T005, T032. Trazabilidad: FR-021, FR-022.
- [ ] T067 [P] [US6] Escribir primero componentes/lista y consulta de>=3páginas: anterior/siguiente, estados vacío/error/loading/parcial/ilegible, confidencias y evidencia distinguida del tiempo de reproducción. Respuestas fuera de orden/fuente/epoch/track/TTL no restauran ficha; mantener solo página y selección actuales. Rutas: `frontend/tests/features/VideoTrackList.test.tsx`, `frontend/tests/features/VideoTrackDetails.test.tsx`, `frontend/tests/features/useVideoTrackResults.test.tsx`. Dependencias: T005, T059. Trazabilidad: FR-021, FR-022, FR-024.
### Implementación y verificación

- [ ] T068 [US6] Extender apiTypes/parsers sin romper contratos de imagen: «track_id local al video; detection_id no es ID de trayectoria.» Exigir track_id>=1 para video y no sustituir por índice. Referencias «enteros únicos no negativos y, con frame_count confirmado, menores que ese conteo.»; max20elementos según schema. Preservar provenance opcional; histórico desconocido no se deriva de used_enhancement ni del frame visible. Rutas: `frontend/src/services/apiTypes.ts`. Dependencias: T066, T059. Trazabilidad: FR-021, FR-022, FR-026.
- [ ] T069 [US6] Crear consulta de resultados por identidad completa con AbortSignal, minTTL, page_size25 y páginas1..N; «Página anterior y ficha anterior se reemplazan; hidden no suspende limpieza.» Cancelar consulta vieja al cambiar página/fuente, comprobar epoch/generation/videoJobId/enrichmentJobId y trackId para ficha; no caché/historial/descarga de todas las páginas ni POST de inferencia. Rutas: `frontend/src/features/video-analysis/useVideoTrackResults.ts`. Dependencias: T068, T067. Trazabilidad: FR-021, FR-024.
- [ ] T070 [P] [US6] Crear VideoTrackList paginada25, total y página explícitos, selección por track_id real y controles44px/teclado/foco visible. Mostrar clase/estado, incertidumbre y no confundir observaciones summary.detections con vehículos. Hacer accesibles todos los resultados sin truncamiento silencioso. Rutas: `frontend/src/features/video-analysis/VideoTrackList.tsx`. Dependencias: T069, T067. Trazabilidad: FR-021.
- [ ] T071 [P] [US6] Crear ficha legible con atributos, estado/texto/confianza de placa y procedencia disponible. «cuadro i y, cuando hay metadata confirmada, i/fps del video procesado, distinta de currentTime.» Múltiples cuadros son evidencia disponible sin inventar origen ganador; histórico sin metadata muestra cuadro/desconocido. No crops nuevos, requests007 de imagen ni seguimiento de ficha al reproducir. Rutas: `frontend/src/features/video-analysis/VideoTrackDetails.tsx`. Dependencias: T069, T067. Trazabilidad: FR-021, FR-022.
- [ ] T072 [US6] Integrar consulta/lista/ficha en VideoWorkspace con disposición responsive formal y sin JSON como vista principal. Conservar reproducción/conteo independientes, estados parciales e identidad/limpieza vigentes; ninguna selección/pausa/seek crea lectura o intercambia ficha entre tracks. Rutas: `frontend/src/features/video-analysis/VideoWorkspace.tsx`, `frontend/src/styles.css`. Dependencias: T070, T071, T057. Trazabilidad: FR-021, FR-022, FR-023.
- [ ] T073 [US6] Revisar propuesta con lo realmente entregado: pausa/seek, identificación de tracks del instante, click futuro en contorno o lista, ficha/drawer mobile, foco/teclado/toque, ausencia/expiry y procedencia temporal. Identificar dependencias pendientes de endpoint/índice temporal y asociación frame/track sin cambiar API ni implementar overlays interactivos aquí. Rutas: `specs/008-exploracion-imagen-video/propuesta-inspeccion-video.md`. Dependencias: T072. Trazabilidad: FR-025, SC-010.
- [ ] T074 [US6] Ejecutar E2E de todas las páginas/fichas y evidencia con/sin metadata; pausar/buscar/cambiar página suma0inferencias/POST y0crops exclusivos de imagen. Verificar teclado/mobile, TTL oculto y selección tardía; registrar resultados, revisar propuesta y confirmar incremento. Rutas: `frontend/e2e/video-track-details.spec.ts`, `specs/008-exploracion-imagen-video/validation.md`. Dependencias: T072, T073. Trazabilidad: SC-008, SC-009, SC-010.

**Checkpoint**: US6 se valida con su prueba independiente antes de dar por entregado el incremento.

## Fase 9: Polish — Regresión, mediciones y cierre de implementación

**Objetivo**: Reunir evidencia reproducible de008 sin ocultar fallos ni cerrar pendientes006/007.

**Prueba independiente**: Suites pertinentes, mediciones visuales/recursos y revisión de seguridad documentadas; solo cerrar aceptación integral si todos los gates están acreditados.

### Implementación y verificación

- [ ] T075 Validar respuestas nuevas contra las16defs/13ejemplos válidos y9inválidos del diseño y OpenAPI; asegurar wrappers/rutas delegan en servicios, compatibilidad de nullable históricos, API directa, auth/owners y conteo/raw. Documentar cualquier desviación antes de implementarla, sin cambiar contratos aprobados para hacer pasar tests. Rutas: `tests/contract/test_exploration_008_schemas.py`, `specs/008-exploracion-imagen-video/validation.md`. Dependencias: T074, T065, T044, T027. Trazabilidad: FR-026, FR-028, SC-009.
- [ ] T076 Ejecutar suites completas pertinentes una vez con entorno registrado: pytest, Vitest, build y Playwright existente+config008. Registrar contadores/errores, comprobar006/007/003 y no sustituir fallos por exclusiones; repetir solo tras cambios/fallos nuevos. Mantener archivos generados y cambios previos fuera de commits propios. Rutas: `specs/008-exploracion-imagen-video/validation.md`. Dependencias: T075. Trazabilidad: FR-028, SC-009.
- [ ] T077 Ejecutar3pares completos AB/BA por cada clip del manifiesto con hardware/modelos/pesos/umbrales y calentamiento idénticos; tiempo desde decodificación hasta publicación con encoder, RSS backend+FFmpeg propio muestreado<=100ms. Por clip mediana temporal y máximo pico combinado<=110% baseline, mismo framecount/FPS/resolución/duración (tolerancia1cuadro); registrar todas las corridas/fallos. Reportar RSS gateway y coste enrichment separado, UI/health<=1s; si falta equipo/modelos o falla gate, conservar tarea y SC-006 pendientes. Rutas: `scripts/evaluate_video_presentation.py`, `specs/008-exploracion-imagen-video/video-presentation-summary.json`, `specs/008-exploracion-imagen-video/validation.md`. Dependencias: T076, T042. Trazabilidad: FR-015, FR-027, SC-006.
- [ ] T078 Revisar canario0 en build/HTML/red/logs/repos/informes, ingreso local/privado, auth/owners, caps/cookies/CSRF/Range, cierre de streams y recursos al reset/TTL durante cuerpo/pausa. Confirmar sesiones acotadas<=128por defecto y cleanup<=2s, página/ficha actual únicamente y ningún medio/OCR/secret/path privado versionado; registrar casos y evidencia segura. Rutas: `specs/008-exploracion-imagen-video/validation.md`. Dependencias: T077. Trazabilidad: FR-005, FR-024, FR-027, SC-002.
- [ ] T079 Revisar capturas controladas en360/768/1440 y texto200% de carga/vacío/error/éxito/parcial, tabs/zoom/lista/reproductor/conteo; contraste, etiquetas, foco/teclado/toque44px, colores sólidos y ausencia de rótulos sobre vehículos. Documentar revisión humana y límites; no afirmar certificación WCAG completa. Rutas: `specs/008-exploracion-imagen-video/validation.md`. Dependencias: T078. Trazabilidad: FR-003, SC-001, SC-004.
- [ ] T080 Actualizar README y quickstart con comandos comprobados, .env.web.example ficticio, procesos/puertos, límites/TTL, principio único por gateway y requisito de HTTPS/ingreso remoto autenticado preexistente. Explicar recuperación por intención, progreso, referencias CFR y alcance de pausa futura; no registrar valores privados ni prometer mejora OCR. Rutas: `README.md`, `specs/008-exploracion-imagen-video/quickstart.md`. Dependencias: T079, T073. Trazabilidad: FR-004, FR-025, FR-026.
- [ ] T081 Completar matriz de28FR/10SC/27escenarios y5principios con prueba/medida/evidencia, estado logrado/fallido/pendiente y comandos ejecutados. Distinguir sintético vs benchmark completo; conservar006/T067–T068 y007/T061–T064/T070, no cerrar OCR real. Un gate fallido/no ejecutado impide afirmar aceptación integral y deja su tarea abierta. Rutas: `specs/008-exploracion-imagen-video/audit.md`, `specs/008-exploracion-imagen-video/tasks.md`. Dependencias: T080. Trazabilidad: FR-027, FR-028, SC-009, SC-010.
- [ ] T082 Revisar diff contra baseline y conservar feature/008-exploracion-imagen-video/check-out principal/cambios previos; comprobar que solo código/documentación propios entran al commit final de implementación. Registrar hash/resultados/pendientes y preparar siguiente converge; no push ni cierre ficticio si faltan gates. Rutas: `specs/008-exploracion-imagen-video/validation.md`, `specs/008-exploracion-imagen-video/audit.md`. Dependencias: T081. Trazabilidad: SC-010.

**Checkpoint**: Registrar evidencia y pendientes; no alterar el alcance de las historias.

## Dependencias y orden

```text
Setup T001–T003 -> Foundation T004–T005
Foundation -> US1 (T006–T012, MVP)
Foundation -> US2 (T013–T027); integra US1 al cerrar transporte
US2 -> US4 (T028–T044); algoritmo backend testeable sin navegador
US2 + US4 -> US5 (T045–T059)
US1 + US2 -> US3 (T060–T065); independiente de inferencias de video
US4 + US5 -> US6 (T066–T074)
US1 + US2 + US3 + US4 + US5 + US6 -> Polish (T075–T082)
```

Los tests puros pueden prepararse tan pronto esté listo su arnés; el grafo describe cierre/integración, no exige arrancar modelos para probar reductores o geometría. US3 puede adelantarse tras US2 si se respeta exclusión de archivos compartidos. US6 usa metadatos de US4 y estado de US5; su consulta/lista se prueba aisladamente con contratos controlados. No ejecutar a la vez tareas que tocan apiTypes.ts, App.tsx, styles.css, stores o validation.md aunque pertenezcan a historias distintas.

## Ejemplos de paralelismo por historia

| Historia | Tareas que pueden ejecutarse juntas | Condición |
|---|---|---|
| US1 | T006 + T007; después T008 + T009 | Arneses listos; tests primero, archivos distintos |
| US2 | T013 + T014 + T015; T017 + T018 | Tests listos y T016 completada antes de T018; rutas/política y sesiones separados |
| US4 | T028 + T029 + T030 + T039; T033 junto con T034 | Arneses listos; para implementación, paleta/modelos y pruebas correspondientes listos |
| US5 | T045 + T046 + T047; T052 junto al backend T048–T051 | Gateway y arneses listos; reducer no comparte archivos con stores/proxy |
| US3 | T060 + T061 | Navegación/arnés listos; geometría/componente/integración posteriores son secuenciales |
| US6 | T066 + T067; después T070 + T071 | Estado/metadatos disponibles; parsers/consulta y pruebas verdes antes de componentes paralelos |

Setup permite T002 + T003 tras T001; Foundation permite T004 + T005. Se identifican 29 tareas [P]; las demás tienen dependencias o comparten archivos. Paralelismo de tareas no significa ejecución simultánea de benchmarks: las mediciones pareadas requieren carga comparable y un job por brazo.

## Estrategia de entrega

1. **MVP de navegación**: T001–T012; demostrar modos, persistencia/TTL y accesibilidad con el transporte anterior temporal. No atribuir aún configuración segura ni análisis de video mejorado.
2. **Configuración administrada**: US2, con imagen006/007 funcional por gateway y API key inaccesible al navegador.
3. **Video limpio y automático**: US4 y US5; presentación raw intacta, progreso veraz, medio disponible pronto y recuperación idempotente. Los gates de fluidez/recursos permanecen abiertos hasta medirse.
4. **Exploración**: US3 añade zoom local; US6 lista/ficha paginada y revisión de propuesta futura de pausa/selección, sin implantar contornos clicables temporales.
5. **Cierre**: ejecutar suites pertinentes y protocolo, completar auditoría y commit. Si falta algún gate, documentar claramente el pendiente y no declarar implementación integral aceptada.

## Trazabilidad de requisitos y aceptación

| Requisito | Tareas responsables |
|---|---|
| FR-001 | T006, T010 |
| FR-002 | T006, T010 |
| FR-003 | T007, T011, T079 |
| FR-004 | T013, T015, T022, T080 |
| FR-005 | T013, T020, T047, T078 |
| FR-006 | T014, T015, T020 |
| FR-007 | T013, T022 |
| FR-008 | T060, T062, T063 |
| FR-009 | T060, T063, T064 |
| FR-010 | T060, T062, T064 |
| FR-011 | T060, T063, T064 |
| FR-012 | T028, T031, T035, T039, T041 |
| FR-013 | T028, T033, T041, T055 |
| FR-014 | T028, T033, T035 |
| FR-015 | T029, T035, T036, T077 |
| FR-016 | T045, T046, T047, T048, T049, T050, T051, T053, T057 |
| FR-017 | T029, T032, T034, T039, T040, T046, T052, T056 |
| FR-018 | T034, T045, T049, T050, T053 |
| FR-019 | T046, T050, T052, T053, T056, T057 |
| FR-020 | T046, T053, T054, T055, T056 |
| FR-021 | T066, T067, T068, T069, T070, T071, T072 |
| FR-022 | T066, T067, T068, T071, T072 |
| FR-023 | T035, T054, T055, T057, T072 |
| FR-024 | T006, T014, T020, T029, T036, T037, T038, T045, T046, T048, T051, T052, T054, T055, T057, T067, T069, T078 |
| FR-025 | T073, T080 |
| FR-026 | T001, T003, T031, T035, T064, T068, T075, T080 |
| FR-027 | T001, T037, T042, T059, T077, T078, T081 |
| FR-028 | T003, T075, T076, T081 |
| SC-001 | T007, T012, T079 |
| SC-002 | T013, T026, T027, T078 |
| SC-003 | T002, T061, T065 |
| SC-004 | T002, T030, T042, T043, T079 |
| SC-005 | T002, T030, T033, T042, T043 |
| SC-006 | T030, T077 |
| SC-007 | T058, T059 |
| SC-008 | T058, T074 |
| SC-009 | T001, T003, T012, T026, T038, T043, T058, T065, T074, T075, T076, T081 |
| SC-010 | T044, T073, T074, T081, T082 |

Los27 escenarios de aceptación se verifican por historia y se enumeran con evidencia en T081; los10SC requieren resultados medidos o estado pendiente explícito. Matriz constitucional: I(modularidad/contratos) T004/T017/T022/T075; II(validación/errores/trazas) T014/T020/T029/T037/T078; III(privacidad/retención) T013–T026/T038/T051/T078; IV(pruebas/calidad sin cambiar modelo) T003/T028–T030/T060–T061/T075–T076; V(recursos medibles) T019–T021/T036–T042/T077.

## Comandos de verificación previstos

Desde raíz, con entorno ya instalado y sin actualizar dependencias fuera del plan:

~~~powershell
.venv/Scripts/python.exe -B -m pytest -o addopts='' -q
npm --prefix frontend run test
npm --prefix frontend run build
# Desde frontend (primero suite anterior, luego config nueva):
./node_modules/.bin/playwright.cmd test --reporter=json
./node_modules/.bin/playwright.cmd test --config=playwright.008.config.ts --reporter=json
~~~

Generador/evaluador y condiciones: [quickstart](quickstart.md) y [protocolo](validation-protocol.md). Son comandos futuros de implement, no verificaciones de producto ejecutadas al generar este backlog. La aceptación exige conservar todos los cuadros y medir modelos/dispositivo efectivos; fixtures no acreditan exactitud real de detección/OCR. Los pendientes006/T067–T068 y007/T061–T064/T070 continúan independientes.
