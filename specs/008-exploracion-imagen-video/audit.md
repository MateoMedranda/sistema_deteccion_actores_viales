# Auditoría de implementación008

Rama feature/008-exploracion-imagen-video, checkout principal. Implementación funcional terminada; T077/SC-006 y T079 siguen abiertos por las verificaciones externas descritas abajo. No se declara aceptación integral. Las referencias usan datos sintéticos propios y conservan los pendientes006/T067–T068 y007/T061–T064/T070. No se acredita mayor exactitud OCR.

## Requisitos funcionales

Estado funcional implementado salvo el cierre de coste señalado; los resultados finales ejecutados se registran en validation.md. «Implementado» no convierte por sí solo un gate en PASS.

| FR | Alcance | Evidencia |
|---|---|---|
| FR-001 | Navegación superior | WorkspaceTabs; workspace-navigation.spec.ts |
| FR-002 | Estado conservado por modo | workspacesLifecycle.test.tsx; video-analysis-flow.spec.ts |
| FR-003 | Responsive/teclado/200% | image-analysis.accessibility.spec.ts; scene-viewport.spec.ts; video-track-details.spec.ts |
| FR-004 | Entorno administrado | WebSettings; test_web_policy.py; managed-session.spec.ts |
| FR-005 | Clave privada | test_web_gateway_security.py; managed-session.spec.ts |
| FR-006 | Estados seguros | ConnectionStatus; test_web_gateway_proxy.py; managed-session.spec.ts |
| FR-007 | Propietario y reset | test_web_gateway_security.py; session-convergence.spec.ts |
| FR-008 | Zoom hasta400% | SceneViewport; scene-viewport.spec.ts |
| FR-009 | Pan/teclado/arrastre | SceneViewport.test.tsx; sceneViewportGeometry.test.ts |
| FR-010 | Geometría/identidad/crops | scene-viewport.spec.ts; image-analysis.acceptance.spec.ts |
| FR-011 | Zoom sin cómputo/renovación | scene-viewport.spec.ts; TTL del source se conserva |
| FR-012 | Paleta/leyenda/sin rótulos | test_class_presentation.py; VideoLegend; video-presentation.spec.ts |
| FR-013 | Alineación temporal | test_video_presentation.py; evaluate_video_presentation.py |
| FR-014 | Filtro solo visual | test_video_presentation.py; golden raw y huellas del benchmark |
| FR-015 | Coste aprobado | T077/SC-006 pendientes; no se omiten cuadros |
| FR-016 | Autoencadenado idempotente | test_job_idempotency.py; test_web_gateway_intents.py; useVideoAnalysis.test.tsx |
| FR-017 | Progreso real separado | test_video_job_phases.py; VideoProgress.test.tsx; video-analysis-flow.spec.ts |
| FR-018 | Evidencia existente por track | EnrichmentJobService; test_job_idempotency_concurrency.py |
| FR-019 | Recuperación independiente | useVideoAnalysis.test.tsx; video-analysis-flow.spec.ts |
| FR-020 | Reproducción temprana | VideoPlayer.test.tsx; video-analysis-flow.spec.ts |
| FR-021 | Lista/ficha completa | videoEvidenceParsing.test.ts; useVideoTrackResults.test.tsx; video-track-details.spec.ts |
| FR-022 | Referencia distinta de currentTime | VideoTrackDetails.test.tsx; video-track-details.spec.ts |
| FR-023 | Reproducción/conteo | video-count-regression.spec.ts; videoCountIdentity.test.tsx; LineEditor |
| FR-024 | Menor TTL/respuestas tardías | test_web_gateway_body_deadlines.py; session-convergence.spec.ts; lifecycle y hooks |
| FR-025 | Propuesta revisada | propuesta-inspeccion-video.md |
| FR-026 | Compatibilidad | test_008_legacy_compatibility.py; test_exploration_008_schemas.py; suites006/007/003 |
| FR-027 | Medidas reproducibles | baseline.json; zoom-summary.json; video-presentation-summary.json; T077 pendiente |
| FR-028 | Regresiones y límites | validation.md; suites completas; aceptación OCR006/007 sigue abierta |

## Criterios de éxito

| SC | Estado/evidencia |
|---|---|
|001|Recorridos de tabs y200% en360/768/1440; retención/TTL por hooks y navegador.|
|002|Gateway separado, política protegida, bootstrap seguro; canario/ausencia de X-API-Key en navegador.|
|003|Medición final de10escenas/3densas/50puntos por escala y>=30operaciones por viewport en zoom-summary.json.|
|004|Presentación controlada; caso adicional de cruce opuesto reservado antes de medir. Sin texto identificador en renderer nuevo.|
|005|Jitter/IoU/lag por segmento en video-presentation-summary.json; no equivale a calidad del detector real.|
|006|Pendiente de aceptación completa. Las medidas logradas y cualquier fallo se conservan sin ajustar el conjunto reservado.|
|007|Recorridos de fases/espera/recuperación/cero elegibles/parcial/cancelado/TTL; estados y unidades reales.|
|008|61resultados/3páginas con track real, referencias temporales y0POST/crops de imagen al consultar.|
|009|Contadores finales de regresión en validation.md; pendientes anteriores conservados.|
|010|Propuesta revisada con dependencias de índice temporal y pausa/selección futura, accesibilidad y retiro por TTL.|

## Los27 escenarios de aceptación

Se conserva el orden de la spec. No se atribuyen métricas reales a mocks.

| Escenario | Evidencia y alcance |
|---|---|
|US1.1|workspace-navigation: tabs por teclado/toque, estado activo.|
|US1.2|workspacesLifecycle y video-analysis-flow: estado/TTL oculto, sin inferencia adicional.|
|US1.3|workspace-navigation y accesibilidad: foco, teclado/toque y200% en3 tamaños.|
|US1.4|workspacesLifecycle/video-analysis-flow: TTL sigue activo mientras el panel está oculto.|
|US2.1|managed-session: entorno válido sin formulario ni clave de navegador.|
|US2.2|test_web_gateway_security y managed-session: ausente/inválida/indisponible/rechazo seguros.|
|US2.3|Canario de sesión, inspección de headers y privacy-summary:0 credenciales reales en artefactos/diff.|
|US2.4|session-lifecycle/session-convergence: reset/rechazo retira evidencia y conserva entorno.|
|US1.3|workspace-navigation y capturas200%: controles y jerarquía.|
|US2.1|managed-session: bootstrap real controlado sin formulario de credencial.|
|US2.2|test_web_gateway_security: ausente/inválido/rechazo/indisponible seguros.|
|US2.3|managed-session y canario: sin clave en navegador.|
|US2.4|session-lifecycle/convergence: retiro y nuevo epoch con configuración conservada.|
|US3.1|scene-viewport: imagen/cajas comparten escala y proporción.|
|US3.2|SceneViewport: umbral6px, captura, clic suprimido, cancel/blur, flechas.|
|US3.3|image-analysis.acceptance y zoom: selección/crops originales por detección.|
|US3.4|scene-viewport: zoom no emite POST/previewGET ni rótulos.|
|US4.1|Paleta JSON compartida, test_class_presentation y VideoLegend.|
|US4.2|Jitter/IoU/lag del evaluador contra referencia independiente.|
|US4.3|test_video_presentation: corte/hueco/ausencia/clase/degeneradas.|
|US4.4|Video nativo y geometría/FPS/frame_count medidos del output.|
|US4.5|T077 pendiente: no declarar coste integral certificado.|
|US5.1|video-analysis-flow:1upload+1enrichment y GET real tras recibo.|
|US5.2|encoding/publishing indeterminados; unidades separadas en VideoProgress.|
|US5.3|Medio disponible antes de enrichment; fallo conserva medio.|
|US5.4|Reintento nuevo de enrichment conserva video; lista distingue parciales.|
|US5.5|Cero elegibles no crea POST y muestra no aplicable.|
|US5.6|Reducer/hook y session-convergence: no restaurar estado viejo tras cambio/reset/TTL/acceso.|
|US6.1|VideoTrackList/Details: track_id real, atributos/placa/procedencia conocida.|
|US6.2|video-track-details recorre todas las páginas sin descargar historial.|
|US6.3|Cuadro i e i/fps etiquetados como video procesado; no OCR en reproducción.|
|US6.4|Propuesta de inspección revisada; ningún overlay clicable de video implementado.|

## Constitución

| Principio | Evidencia |
|---|---|
|I — Modularidad/contratos|Gateway sin importar runtime de modelos; rutas delegan en servicios; DTOs aditivos y ejemplos JSONSchema.|
|II — Validación/errores/trazas|Allowlist, límites, errores seguros, fases/outcomes reales; pruebas de publicación/cancelación.|
|III — Seguridad/retención|Cookie opaca/CSRF/Host/Origin, API key privada, propietario upstream, mínimo TTL y cleanup; sin historial.|
|IV — Pruebas/calidad del modelo|Pruebas primero por historia y guardas006/007/003. Pesos/tracker/raw/umbral/política OCR preservados; no afirmar precisión nueva.|
|V — Recursos medibles|Streaming/cupos/encoder reap/colas y medidas pareadas. T077 permanece abierto si falta cualquier evidencia de coste.|

## Decisiones de implementación

X-UI-Intent-Generation es una guarda monotónica opcional del gateway, documentada en contracts/gateway.md. No cambia la autenticación ni el contrato directo. Las dos referencias actuales son por operación y conservan la intención tras respuesta para recuperar aceptación incierta.

Los estados de resultados pertenecen a useVideoTrackResults (página actual y ficha), separados del reducer de procesamiento/enriquecimiento. Client/epoch montado, generación y IDs de fuente/job forman la identidad; cambiarla aborta y retira datos antes de aceptar respuestas nuevas.

Solo MP4 figura en la política web porque el validador existente admite MP4/H.264. No se amplía el backend a QuickTime por un ejemplo de diseño que permita varios media_types.

## Siguiente revisión

Ejecutar converge contra el commit final; no cerrar pendientes de OCR ni repetir el análisis de clips privados sin datos/autorización apropiados. El siguiente incremento propuesto es inspección pausada con índice temporal autorizado, no inferencia por seek.

## Pendientes concretos

- **T077 / SC-006**: procesamiento real y presentación sintética pasan en7clips/3pares cada uno. Los modelos reales no produjeron tracks sobre las figuras sintéticas (raw vacío confirmado por huella); esos clips no permiten medir un enriquecimiento real representativo. Faltan clips autorizados con vehículos/placas elegibles, coste real de enriquecimiento separado, RSS del gateway e interacción/health bajo esa carga integrada. El PASS del procesador no sustituye esas medidas.
- **T079**: revisión humana completa de capturas/estados en los tres tamaños. Se realizó inspección visual por el agente y guardas automatizadas; no hubo revisor humano ni certificación WCAG. Las capturas controladas del último recorrido quedan en frontend/test-results; no se versionan imágenes privadas.
- Se conservan íntegros los pendientes006/T067–T068 y007/T061–T064/T070. No se cambió baseline-v1 de OCR.

Los cierres de código y sus commits no cierran esos gates. La revisión siguiente puede centrarse en estos pendientes y cualquier divergencia adicional que encuentre converge.

## Resultado de las suites

286 pytest,100 Vitest/43archivos,159 casos únicos de navegador y build PASS. Zoom<=0.02917px y p95<=105.5ms. Los159 corresponden a114regresiones y45casos008, con repetición solo de los fallos corregidos. Cierre80/82; T077/T079 conservan el estado pendiente.
