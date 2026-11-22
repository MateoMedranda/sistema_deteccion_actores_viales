# Specification Analysis Report — 008

**Fecha**: 2026-11-21. **Rama**: feature/008-exploracion-imagen-video. **Base analizada**: 208355d (etapa tasks), con plan 05d3a7a.

**Resultado**: 3 hallazgos MEDIUM; 0 HIGH y 0 CRITICAL. Los38 requisitos tienen tareas asociadas, con una cobertura semántica parcial en FR-012. Se puede iniciar trabajo independiente; conviene resolver estos detalles antes de implementar los bloques afectados T032/T041/T051. No se declara aceptación de producto.

## Alcance y conservación

Análisis de spec.md, plan.md, tasks.md y constitución1.0.0; consulta dirigida de data-model.md, contratos/schema y protocolo para resolver el significado de las tareas. La lectura puntual de la configuración/servicio de enriquecimiento confirma que la elegibilidad procede del servidor y que no debe copiarse al catálogo visual.

La solicitud explícita de guardar/confirmar esta etapa autoriza este informe nuevo. No se aplicaron correcciones a especificación, plan, tareas, contratos o código. Se mantiene el checkout principal y la rama existente; cambios previos y sesiones históricas de métricas quedan fuera del commit del informe.

## Hallazgos

| ID | Categoría | Severidad | Ubicación | Resumen | Recomendación |
|---|---|---|---|---|---|
| I1 | Inconsistencia | MEDIUM | contracts/gateway.md:L33/L38/L76; tasks.md:L141/L147 (T047/T051) | La allowlist del gateway presenta la intención como opcional para los dos POST, mientras la sección normativa y T051 la exigen para upload/enriquecimiento de video. El carácter opcional del header de backend no equivale al de X-UI-Intent del gateway. | Precisar en la tabla: X-UI-Intent obligatorio para video y enriquecimiento source.kind=video; opcional para imagen legacy. Mantener Idempotency-Key opcional solo en API directa. Añadir casos de ausencia por cada modalidad a T047. |
| I2 | Inconsistencia | MEDIUM | data-model.md:L67/L72/L77; contracts/schemas.json:L274; tasks.md:L111 (T032) | El modelo anuncia adiciones nullable para históricos y conserva null, pero frame_total_confirmed solo admite booleano en la tabla y el schema. Una implementación que aplique null a todos los campos históricos será incompatible; no queda explícito el valor de migración/serialización de ese flag. | Declarar la excepción del flag: false significa no confirmado para históricos (o fijar expresamente ausencia en el contrato legacy); reservar null a los campos que lo admiten. Alinear migración/parser y ejemplos/pruebas de T029/T032/T039. No inferir metadatos históricos. |
| U1 | Subespecificación / cobertura parcial | MEDIUM | spec.md:L150 (FR-012); contracts/frontend-interactions.md:L44; contracts/schemas.json:L110; data-model.md:L74; tasks.md:L124 (T041) | FR-012 pide tratamiento explícito de clases no enriquecibles. T041 remite la elegibilidad al backend y prohíbe inferirla de la paleta, pero los contratos solo aportan classes_present y un eligible_track_count global; las capacidades también son globales. En una escena mixta, no está definido el dato o mensaje que permite explicar las clases no enriquecibles sin inventar su elegibilidad. | Definir el comportamiento de la leyenda: si debe distinguir cada clase, añadir una señal explícita y no sensible del servidor con semántica de elegibilidad, y tareas de contrato/parser/UI; si se pretende un aviso general, describir su texto/condición sin afirmar elegibilidad individual. Probar mezcla elegible/no elegible/desconocida sin codificar vehicle_classes en frontend. |

### Interpretación y límites

I1 se refiere al contrato del relay web: el header de la API backend es opcional para compatibilidad y puede seguir siéndolo. No se propone eliminar la guarda de intención del flujo nuevo.

I2 identifica la redacción incompatible de históricos, no un fallo ya observado en una migración: todavía no se ejecuta implementación008. El schema admite ausencia del flag legacy y rechaza null cuando se incluye; ready exige true y metadatos. El documento debe elegir una serialización inequívoca.

U1 es cobertura parcial de una cláusula de FR-012, no ausencia total de implementación de la paleta/video. No se requiere exponer Settings, cambiar clases/modelos o ampliar inferencias; falta fijar el mensaje o señal de elegibilidad que la experiencia presentará.

No se detectan duplicados funcionales que deban consolidarse. La separación navegación/retención, progreso/disponibilidad del medio y filtros/raw/conteo es deliberada. “Formal”, “fluido” y “preciso” quedan vinculados a viewports, geometría, jitter, IoU, lag y presupuestos medibles. No hay placeholders de decisión abiertos; las menciones a placeholders del ejemplo de entorno son restricciones, no TODOs.

## Coverage Summary Table

Cobertura de asociación: un requisito tiene al menos una tarea identificable. Este porcentaje no acredita implementación ni suficiencia de cada cláusula; FR-012 mantiene U1.

| Requirement Key | Has Task? | Task IDs | Notes |
|---|---|---|---|
| FR-001 | Sí | T006, T010 | Cubierto por tareas; pendiente de ejecutar en implement. |
| FR-002 | Sí | T006, T010 | Cubierto por tareas; pendiente de ejecutar en implement. |
| FR-003 | Sí | T007, T011, T079 | Cubierto por tareas; pendiente de ejecutar en implement. |
| FR-004 | Sí | T013, T015, T022, T080 | Cubierto por tareas; pendiente de ejecutar en implement. |
| FR-005 | Sí | T013, T020, T047, T078 | Cubierto por tareas; pendiente de ejecutar en implement. |
| FR-006 | Sí | T014, T015, T020 | Cubierto por tareas; pendiente de ejecutar en implement. |
| FR-007 | Sí | T013, T022 | Cubierto por tareas; pendiente de ejecutar en implement. |
| FR-008 | Sí | T060, T062, T063 | Cubierto por tareas; pendiente de ejecutar en implement. |
| FR-009 | Sí | T060, T063, T064 | Cubierto por tareas; pendiente de ejecutar en implement. |
| FR-010 | Sí | T060, T062, T064 | Cubierto por tareas; pendiente de ejecutar en implement. |
| FR-011 | Sí | T060, T063, T064 | Cubierto por tareas; pendiente de ejecutar en implement. |
| FR-012 | Sí, parcial | T028, T031, T035, T039, T041 | Parcial: falta cerrar tratamiento de no enriquecibles (U1). |
| FR-013 | Sí | T028, T033, T041, T055 | Cubierto por tareas; pendiente de ejecutar en implement. |
| FR-014 | Sí | T028, T033, T035 | Cubierto por tareas; pendiente de ejecutar en implement. |
| FR-015 | Sí | T029, T035, T036, T077 | Cubierto por tareas; pendiente de ejecutar en implement. |
| FR-016 | Sí | T045, T046, T047, T048, T049, T050, T051, T053, T057 | I1 debe aclarar obligatoriedad por modalidad. |
| FR-017 | Sí | T029, T032, T034, T039, T040, T046, T052, T056 | I2 debe aclarar flag histórico. |
| FR-018 | Sí | T034, T045, T049, T050, T053 | Cubierto por tareas; pendiente de ejecutar en implement. |
| FR-019 | Sí | T046, T050, T052, T053, T056, T057 | Cubierto por tareas; pendiente de ejecutar en implement. |
| FR-020 | Sí | T046, T053, T054, T055, T056 | Cubierto por tareas; pendiente de ejecutar en implement. |
| FR-021 | Sí | T066, T067, T068, T069, T070, T071, T072 | Cubierto por tareas; pendiente de ejecutar en implement. |
| FR-022 | Sí | T066, T067, T068, T071, T072 | Cubierto por tareas; pendiente de ejecutar en implement. |
| FR-023 | Sí | T035, T054, T055, T057, T072 | Cubierto por tareas; pendiente de ejecutar en implement. |
| FR-024 | Sí | T006, T014, T020, T029, T036, T037, T038, T045, T046, T048, T051, T052, T054, T055, T057, T067, T069, T078 | Cubierto por tareas; pendiente de ejecutar en implement. |
| FR-025 | Sí | T073, T080 | Cubierto por tareas; pendiente de ejecutar en implement. |
| FR-026 | Sí | T001, T003, T031, T035, T064, T068, T075, T080 | Cubierto por tareas; pendiente de ejecutar en implement. |
| FR-027 | Sí | T001, T037, T042, T059, T077, T078, T081 | Cubierto por tareas; pendiente de ejecutar en implement. |
| FR-028 | Sí | T003, T075, T076, T081 | Cubierto por tareas; pendiente de ejecutar en implement. |
| SC-001 | Sí | T007, T012, T079 | Cubierto por tareas; pendiente de ejecutar en implement. |
| SC-002 | Sí | T013, T026, T027, T078 | Cubierto por tareas; pendiente de ejecutar en implement. |
| SC-003 | Sí | T002, T061, T065 | Cubierto por tareas; pendiente de ejecutar en implement. |
| SC-004 | Sí | T002, T030, T042, T043, T079 | Cubierto por tareas; pendiente de ejecutar en implement. |
| SC-005 | Sí | T002, T030, T033, T042, T043 | Hipótesis versionada, requiere medición; no PASS por diseño. |
| SC-006 | Sí | T030, T044, T077 | T077 requiere corridas completas pareadas y RSS combinado. |
| SC-007 | Sí | T058, T059 | Cubierto por tareas; pendiente de ejecutar en implement. |
| SC-008 | Sí | T058, T074 | Cubierto por tareas; pendiente de ejecutar en implement. |
| SC-009 | Sí | T001, T003, T012, T026, T038, T043, T058, T065, T074, T075, T076, T081 | Pendientes006/007 se conservan independientes. |
| SC-010 | Sí | T044, T073, T074, T081, T082 | Propuesta futura; selección sobre video pausado fuera del código008. |

### Historias y escenarios

| Historia | Prioridad | Tareas | Cierre independiente |
|---|---|---|---|
| US1 | P1 | T006–T012 (7) | Navegación teclado/toque, estado/TTL oculto, sin POST/cancel adicionales. |
| US2 | P1 | T013–T027 (15) | Entorno y conexión segura, canario, límites/Range y cliente directo compatible. |
| US4 | P1 | T028–T044 (17) | Paleta/raw intactos, fases/publicación, IoU/lag/jitter medidos. |
| US5 | P1 | T045–T059 (15) | Una intención/cola, progreso independiente, recuperación y video utilizable temprano. |
| US3 | P2 | T060–T065 (6) | Zoom/pan hasta400%, error<=1px, p95<=200ms, misma selección/crops. |
| US6 | P2 | T066–T074 (9) | Todas las páginas, track ID y referencias de evidencia correctos, sin inferencias nuevas. |

Preparación T001–T005 (5) y cierre T075–T082 (8). Los27 escenarios de aceptación se distribuyen en US1=4, US2=4, US3=4, US4=5, US5=6 y US6=4. Las historias tienen pruebas independientes; el MVP se limita a T001–T012 y conserva temporalmente transporte previo de manera explícita.

## Constitution Alignment Issues

No se identifican conflictos con los5 principios ni necesidad de modificar la constitución:

| Principio | Evidencia de planificación/tareas |
|---|---|
| I: arquitectura modular/contratos | Gateway ligero sin app.main/modelos, política con servicio, helpers puros y transportes; T004/T017/T022/T075. |
| II: validación/errores/trazas | Guardas previas a upload, allowlist/cotas/deadlines, errores seguros y desenlace efectivo; T014/T019–T020/T029/T037. |
| III: seguridad/retención | Key server-only, ingreso local/privado autorizado, auth/owners preservados, sesiones/TTL/streams acotados; T013–T026/T038/T051/T078. |
| IV: pruebas/calidad del modelo | Casos nuevos primero, regresión imagen/video/conteo, raw y modelos sin cambios; T003/T028–T030/T060–T061/T075–T076. |
| V: recursos/medición | Sin segunda carga de modelos; retención de cupo hasta reap, coste completo y RSS FFmpeg incluidos; T019–T021/T036–T042/T077. |

El ingreso remoto autorizado es una condición de despliegue existente, no una excepción ni autenticación aportada por Origin/cookie. Los PASS del plan son de diseño, no resultados de rendimiento/fluidez. Ningún hallazgo exige diluir una regla constitucional.

## Unmapped Tasks

Ninguna sin propósito mapeado. T004/T005 no repiten IDs de requisitos, pero son arneses comunes de FR-028/principioIV; las tareas sin FR explícito dentro de historias se asocian por el producto descrito y su US. Los cierres/documentación tienen trazabilidad de entrega y no representan funcionalidades extra.

## Metrics

| Métrica | Resultado |
|---|---:|
| Requisitos funcionales | 28 |
| Criterios de éxito que requieren trabajo verificable | 10 |
| Total inventario | 38 |
| Requisitos con tarea asociada | 38/38 (100%) |
| Requisitos con una cláusula parcialmente especificada | 1 (FR-012) |
| Tareas | 82 |
| Historias / escenarios | 6 / 27 |
| Tareas marcadas [P] | 29 |
| Inconsistencias | 2 |
| Subespecificaciones | 1 |
| Ambigüedades vagas adicionales | 0 |
| Duplicaciones accionables | 0 |
| CRITICAL / HIGH / MEDIUM / LOW | 0 / 0 / 3 / 0 |
| Línea base de puntos existente | 439 PTS; no recalculada ni modificada |

## Verificaciones realizadas

- Prerrequisitos ejecutados una vez: feature resuelta en el checkout principal, spec/plan/tasks presentes.
- IDs T001–T082 únicos/consecutivos, casillas sin completar, fases e historias correctas; dependencias explícitas solo hacia tareas anteriores, sin ciclos.
- Revisión de los ejemplos [P]: pares con archivos diferentes y guardas de dependencias; archivos compartidos se serializan. Benchmarks no se paralelizan entre brazos.
- 43 enlaces locales Markdown revisados en12 documentos:0 rotos. JSON de contratos/ejemplos legible;16 definiciones y referencias internas resueltas,11 ejemplos válidos declarados y7 inválidos declarados.
- No se repitió el validador jsonschema de plan: no está instalado en el entorno del proyecto. El chequeo de esta etapa es estructural; los resultados semánticos de los ejemplos ya registrados en plan no se presentan como una nueva ejecución.
- No se ejecutaron suites de producto, inferencias, builds, OCR ni benchmarks en esta etapa documental. Sus resultados siguen pendientes de implement.
- Hook before_analyze de metricas ejecutado; sesión tareas cerrada y sesión analizar abierta. No hay hook after_analyze registrado.
- Verificación de huellas para conservar todos los artefactos originales y código; commit limitado a este informe.

## Next Actions

1. Resolver I1/I2/U1 con cambios documentales concretos y las pruebas/tareas afectadas. Mantener el número de tareas si las correcciones caben en las existentes; si cambian descripciones, actualizar la línea base PTS mediante el hook correspondiente sin borrar el historial.
2. Repetir el mismo análisis para comprobar consistencia; el informe actual no aplica correcciones por sí solo.
3. Continuar con implement después de decidir esos detalles. No hay bloqueo constitucional; puede prepararse trabajo independiente mientras se resuelven, sin declarar que todo está listo integralmente.

Solicitud sugerida para remediación:

~~~text
Corrige I1, I2 y U1 del análisis de specs/008-exploracion-imagen-video en el checkout principal, conserva feature/008-exploracion-imagen-video y los cambios existentes, vuelve a ejecutar speckit-analyze y haz commit de la etapa.
~~~

Tras la remediación:

~~~text
$speckit-implement SPECIFY_FEATURE_DIRECTORY=specs/008-exploracion-imagen-video implementa en el checkout principal, conserva la rama y los cambios existentes, ejecuta las pruebas y haz commit de esta etapa.
~~~

Las correcciones son propuestas para aprobación posterior; el commit de analyze conserva el diagnóstico original sin alterar los documentos evaluados. La inspección temporal clicable de video sigue siendo una propuesta para la siguiente iteración y los pendientes de aceptación006/007 continúan abiertos.
