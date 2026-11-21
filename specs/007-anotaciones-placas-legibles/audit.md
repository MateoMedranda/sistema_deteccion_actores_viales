# Auditoría de implementación 007

Rama feature/007-anotaciones-placas-legibles, checkout principal. Se implementaron US1/US2/US3 y la parte técnica de US4. La aceptación integral sigue pendiente de referencias reales y del gate OCR; no se confunde con el resultado de las pruebas sintéticas.

| Requisito | Estado y evidencia |
|---|---|
| FR-001 | Verificado: original canónico, sin petición de anotada ni texto/glifos sobre escena. unobstructed.spec.ts, regresión de medios. |
| FR-002 | Verificado: DetectionContext externo, prioridad foco/puntero/selección, IDs sin partir. context.test.tsx y navegador. |
| FR-003 | Verificado: eventos atómicos de contexto, sin sobrescribir resultados ni cambiar selección; prueba de carrera añadida y pasada. |
| FR-004 | Verificado: misma identidad entre contorno/lista/ficha/crops; teclado/toque, cajas pequeñas/superpuestas, escenas y paginación de006. |
| FR-005 | Verificado: registro explícito de13 colores estables, fallback neutral, misma presentación compartida. classPresentation.test.ts, classes.spec.ts. |
| FR-006 | Verificado: ClassLegend con todos los actores; solo eligibility del servidor habilita ficha. |
| FR-007 | Verificado en los controles probados: contorno de clase más trazos claros/oscuros, selección doble, foco, contraste real sobre blanco/negro y lista >=44px. No es certificación WCAG completa. |
| FR-008 | Verificado:360/768/1440, texto200%, sin scroll horizontal global; columnas crecen con tipografía. |
| FR-009 | Verificado: GET autenticado sin modelos; contadores de detector/atributos/localización/OCR no aumentan por preview. |
| FR-010 | Verificado: Original inicial, Procesada explícita, zoom proporcional y desplazamiento local. |
| FR-011 | Verificado: ROI autorizado/half-open, gris/escala entera/CLAHE, PNG sin metadata heredada; sin reconstrucción. |
| FR-012 | Verificado: admite localizadas read/unreadable/failed; not_detected/sin bbox no produce crop inventado. |
| FR-013 | Verificado: preparación, disponible, no aplicable, fallo/reintento y vencimiento; original independiente. |
| FR-014 | Verificado: provenance opcional tipada, intentos y ganador distintos de perfil visual; históricos desconocidos. |
| FR-015 | Evaluador implementado y probado con oráculos/splits/denominadores. Aceptación de exactitud real PENDIENTE. |
| FR-016 | Cumplido: baseline-v1 activa; ninguna ruta/UI/CLI promueve candidata sin decisión explícita respaldada por gate. |
| FR-017 | Verificado: dueño/TTL mínimo, limpieza/aborto, reautorización de caché/publicación, rechazo inmediato y sin respuesta tardía restaurada; menor vigencia de metadata también limita cuerpo/decode. |
| FR-018 | Verificado: CPU1/cero cola, single-flight, límites RAM/LRU, permiso retenido hasta terminar hilo real, purga sin tráfico. |
| FR-019 | Instrumentación y reporte agregado implementados; métricas sintéticas registradas. Coste de evaluación real PENDIENTE. |
| FR-020 | Regresión de imagen/video/conteo pasada; sin cambios a modelos/pesos/umbrales/autenticación ni configuración privada. |

| Criterio | Estado |
|---|---|
| SC-001 | Verificado con10 escenas,3 densas de28, IDs largos, original/anotada distintos, tres viewports/200%. |
| SC-002 | Verificado por asociación/selección de los fixtures, teclado/toque y tiempos monotónicos <1s. |
| SC-003 | Verificado con catálogo, fallback, coherencia y controles reales; capturas revisadas. |
| SC-004 | Verificado:30 comparaciones por viewport, fuente/vehículo/ROI, metadata/PNG y CORS reales con adaptadores sintéticos. |
| SC-005 | Verificado: fallos, TTL, cambios, rechazo, recursos y regresiones anteriores. |
| SC-006 | PENDIENTE: reserva real>=60 y gate de exactitud. |
| SC-007 | Medido en máquina local con30 derivadas frías y30 calientes por viewport; p95<2s. Ver evidence-summary.json. |
| SC-008 | Verificado: límites/single-flight/deadline, purga real sin tráfico<=2s, RSS de proceso acotado durante ciclos. |
| SC-009 | Evaluador técnico verificado; evaluación reproducible con modelos y referencias reales PENDIENTE. |

## Límites y pendientes

T061–T064 y T070 permanecen abiertas. No se dispone de medios/referencias independientes y reserva congelada; no se afirma mayor exactitud. Se conserva baseline-v1 y no se modificó la lectura de video. Los pendientes006/T067 y006/T068 permanecen independientes.

La revisión visual cubre capturas sintéticas, controles y estados implementados. No sustituye la prueba con usuarios de006 ni certifica todas las combinaciones posibles de navegador/hardware.

Los comandos, resultados, mediciones y correcciones están en validation.md y evidence-summary.json. Los cambios se conservan sin commits automáticos ni staging.

## Verificacion posterior de T071-T075 (2026-11-21)

Los cinco hallazgos de convergencia quedaron corregidos y probados. FR-018/SC-005/008 incluyen barreras de acceso a imagenes, SQLite y cache sin bloqueo del loop, retiro temprano y limpieza ante fallos de instrumentacion. FR-002/003/004/007 incluyen contexto visual explicitamente sincronizado entre lista y escena, independiente de la seleccion. FR-005-008/SC-003 incluyen la matriz de13 clases y fallback con estilos efectivos, tres viewports, contraste claro/oscuro y texto200%. FR-019/SC-009 (parte tecnica) incluyen EvaluationRun congelado, mutaciones rechazadas, OpenCV/acelerador y resumen agregado privado.

Validacion:239 pruebas backend,78 frontend, compilacion PASS,3 casos de matriz,6 casos finales de comparacion/rendimiento y24 regresiones adicionales de navegador PASS. Los retrasos y el fallo intermedio de metricas detectados durante este trabajo se corrigieron antes de cerrar las tareas. Datos y limites en [validation.md](validation.md) y [convergence-evidence.json](convergence-evidence.json).

Estas verificaciones no cierran T061-T064/T070 ni acreditan mayor exactitud OCR: continua NOT_RUN y baseline-v1 activa.

## Cierre técnico de T076 (2026-11-21)

Se corrigió la brecha de T075/FR-019/SC-009 (parte técnica): el contexto distingue dispositivo solicitado de observado e incluye el localizador automático, además de detector y OCR. Inventario/políticas previos a inferencia se vinculan a predictores efectivos y se rechazan discrepancias, cambios o procedencia desconocida. Las etapas no ejecutadas quedan explícitas; no se deducen dispositivos desde una configuración genérica.

Evidencia:32 pruebas enfocadas y253 pruebas backend PASS, con casos CPU y CUDA controlados, integración CLI, captura del hook Paddle y privacidad del resumen. Ver [validation.md](validation.md) y [t076-evidence.json](t076-evidence.json). No constituye validación sobre GPU real ni acredita mejora OCR. T061–T064/T070 permanecen pendientes; baseline-v1 no se modifica.
