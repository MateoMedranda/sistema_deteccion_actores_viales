# Auditoría de trazabilidad — 006

Estado: implementación funcional y verificación automatizada realizadas; aceptación final pendiente de T067 y T068. No se han hecho commits ni se han incorporado CSV ajenos. Rama feature/006-mejoras-frontend en checkout principal.

Evidencia común: [validation.md](validation.md), [real-model-smoke.json](real-model-smoke.json) y [usability.md](usability.md). Las siguientes referencias son archivos del repositorio, no afirmaciones de calidad del modelo.

| Requisitos | Implementación / prueba | Estado |
|---|---|---|
| FR-001 | App, VideoJobPanel, CountJobPanel, EnrichmentPanel; video-count-regression.spec.ts | Implementado |
| FR-002 | ImageUpload; validación MIME/extensión/límites en image_validation; flow.spec.ts | Implementado; límite configurado validado por servicio |
| FR-003–FR-006 | useImageAnalysis; lifecycle/pagination/cycleBudget y flow.spec.ts | Implementado |
| FR-007–FR-010 | AnnotatedImageViewer, DetectionList, imageGeometry; selection/accessibility.spec.ts | Implementado |
| FR-011 | VehicleDetails, vehicleView; VehicleDetails.test.tsx | Implementado |
| FR-012 | Detección N, track_id nulo en imagen; selección/regresión | Implementado con DEP-001 pendiente |
| FR-013–FR-015 | EvidenceCrop, plateCrop, normalización de resultados; píxeles y estados de placa | Implementado |
| FR-016 | Estado compartido/foco estable/cierre en flujo; selection.spec.ts | Implementado |
| FR-017–FR-020 | Tokens/CSS scoped, captions y controles; capturas/contraste/texto 200% | Implementado y verificado en entorno controlado |
| FR-021 | ClientError, imageAnalysisMessages, estados/reintentos explícitos | Implementado |
| FR-022–FR-024 | useSessionLifecycle, registro de URLs, generaciones, TTL; session-lifecycle y tests tardíos | Implementado; cancelación remota best-effort |
| FR-025 | B1–B5 y contratos aditivos; suites de contrato y regresión | Implementado; modelos/autenticación conservados |
| FR-026 | Ausencias explícitas, readiness independiente y estados parciales | Implementado |
| FR-027 | Checkout principal/rama feature comprobados | Cumplido |
| FR-028 | PNG RGB sin EXIF, geometría compartida, test EXIF 1–8 | Implementado |
| FR-029 | Elegibilidad del servidor, mínimo TTL, hora de disponibilidad y retirada | Implementado |
| FR-030 | Health por capacidad y ramas independientes; matriz de readiness | Implementado |
| FR-031 | Store atómico, barreras, worker tardío y cancelación en cola | Implementado |
| FR-032 | Janitor periódico, ownership y purga sin tráfico | Implementado |
| FR-033 | normalize_results y esquema de placa; canario ausente en JSON/tablas/respuestas y cliente | Implementado y verificado |
| FR-034 | InferenceMetrics, logs seguros por rama, smoke real | Instrumentación implementada; comparación T067 pendiente |
| SC-001 | Flujo real de pruebas y guard contra duplicados | Verificado con fixtures |
| SC-002 | T081: diez escenas/veinte vehículos distinguibles y 55 resultados/2 páginas en navegador | Verificado con datos controlados; calidad real en T067 |
| SC-003 | T082: 18 mediciones con reloj monotónico, 71.4–87.4 ms, tres viewports | Verificado con datos cargados |
| SC-004 | Geometría, comparación de píxeles, original autorizado y ausencias explícitas | Verificado con fixtures |
| SC-005–SC-006 | Teclado, 3 viewports, 200%, movimiento reducido y contraste muestreado | Verificado en Chromium; no certificación WCAG |
| SC-007 | Cinco participantes | Pendiente, T068 |
| SC-008 | Estados de fallo/parcial/vacío/cancelación/timeout/expiry | Verificado con fixtures |
| SC-009 | Reset, identidad, respuestas tardías y almacenamiento vacío | Verificado con pruebas |
| SC-010 | Imagen/video/conteo/enriquecimiento de video | Verificado con medios controlados |
| SC-011 | Sin seguimiento ficticio en imágenes | Verificado; DEP-001 externo |
| SC-012 | EXIF 1–8 y regiones canónicas | Verificado con fixtures |
| SC-013 | Carreras y purga <=2 s sin solicitudes | Verificado en entorno de pruebas |
| SC-014 | Capacidad real y redacción no read | Verificado, incluyendo carga de modelos reales |
| SC-015 | Instrumentación y 6 imágenes/16 vehículos con modelos reales | Parcial; falta comparación T067 |

## Límites de aceptación

T067 requiere medios/referencia y comparación reproducible. T068 requiere participantes reales. DEP-001 exige un significado/contrato de seguimiento real fuera de esta iteración; no se resuelve renombrando detection_id.

La limpieza local retira referencias y revoca URLs; no promete borrar físicamente bytes ya recibidos ni cancelar inferencia remota al cerrar abruptamente el navegador. Una inferencia iniciada puede terminar internamente, pero sus resultados no se publican tras cancelación/vencimiento.


## Cierre de hallazgos de convergencia

F01–F13 / T070–T082 corregidos y verificados según [convergence-validation.md](convergence-validation.md). La fase 9 de tasks.md describe el estado anterior y conserva sus referencias. Estado actual: 80/82 tareas; T067/T068 y DEP-001 mantienen los límites anteriores. FR-002 obtiene límites efectivos desde /health/image-policy; FR-024 retira acceso rechazado sin esperar cuerpos/otras descargas; FR-032 cubre reinicios mediante recibos de archivos propios. Los ficheros históricos sin propiedad demostrable se preservan, según la limitación documentada.

## Cierre de F14 / T083

FR-034 y la decisión de observabilidad por trabajo/unidad quedan cubiertos también en la ventana final entre comprobación y publicación: el store retorna el desenlace bajo bloqueo y el worker lo usa en enrichment_job. Se preserva completed en inferencias terminadas y no se publican representaciones sensibles tras cancelación/vencimiento. Las seis regresiones deterministas y los resultados posteriores constan en [convergence-validation.md](convergence-validation.md): 166 backend, 52 frontend y 9 recorridos integrados de navegador aprobados. T083 marcada completa; estado vigente 81/83, solo T067 y T068 pendientes. Los cierres anteriores se conservan como historial.
