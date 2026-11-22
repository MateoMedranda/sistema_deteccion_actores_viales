# Specification Analysis Report — 008, revisión tras correcciones

**Fecha**: 2026-11-21. **Rama**: feature/008-exploracion-imagen-video. **Referencia**: informe inicial del commit ebcd532, tareas208355d y plan05d3a7a; esta revisión evalúa las correcciones documentales aprobadas por el usuario.

**Resultado**: 0 hallazgos abiertos (0 CRITICAL/HIGH/MEDIUM/LOW). I1, I2 y U1 resueltos. Los38 requisitos están cubiertos por tareas y ya no queda cobertura parcial en FR-012. La documentación está lista para iniciar implement; el producto, las pruebas runtime y los gates de rendimiento/fluidez siguen pendientes.

## Alcance

Se revisaron spec.md, plan.md, tasks.md y constitución1.0.0, contrastando data-model, contratos JSON/Markdown y protocolo. El usuario aprobó expresamente corregir los3 detalles y repetir analyze, con commit de la etapa. Solo cambian documentos de008 y el CSV de puntos asociado; no se implementó código ni se modificó backend/frontend, modelos, auth o configuración existente.

El informe inicial permanece en el historial Git (ebcd532). Esta versión registra el diagnóstico vigente y las resoluciones; no convierte pruebas futuras en resultados de producto.

## Hallazgos vigentes

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|---|---|---|---|---|---|
| — | — | — | spec.md / plan.md / tasks.md y contratos | Ningún hallazgo abierto en esta revisión. | Continuar con speckit-implement respetando los gates existentes. |

## Resolución de hallazgos anteriores

| ID | Estado | Corrección revisada | Evidencia |
|---|---|---|---|
| I1 | RESUELTO | Gateway exige X-UI-Intent UUID en upload/enriquecimiento de video; imagen admite ausencia. API directa conserva Idempotency-Key opcional. Ausencia requerida/UUID inválido producen422 web_intent_required/web_intent_invalid antes de upstream/cola. | Tabla y sección normativa de contracts/gateway.md; T047/T051 y protocolo coinciden por modalidad. |
| I2 | RESUELTO | frame_total_confirmed es booleano no nullable: false para históricos/no confirmado, NOT NULL DEFAULT 0; null se limita a los otros4 campos permitidos. API008 incluye flag; API anterior puede omitirlo y parser normaliza a false. Null explícito se rechaza. | data-model.md, backend/UI, T029/T032/T039/T040, schema y ejemplos. Si processing_phase está presente, schema exige flag; ready exige true/metadata. |
| U1 | RESUELTO | Leyenda de todas las clases con aviso general de elegibilidad definido literalmente. No se deduce elegibilidad individual de nombres/colores ni se expone matriz de configuración. Desconocidas tienen indicador/fallback y se fijan estados null/vacío/total0. | FR-012, plan, data-model, contrato UI, T039/T041 y protocolo describen escena mixta sin nuevos campos API. |

No se detectan duplicaciones accionables, placeholders de decisión, contradicciones de prioridades ni dependencias cíclicas. Las referencias históricas11/7 del cierre original de plan se identifican expresamente como resultados de aquella etapa; los ejemplos actuales son13/9.

## Coverage Summary Table

La cobertura indica diseño/tarea asociada; no acredita implementación o rendimiento logrado.

| Requirement Key | Has Task? | Task IDs | Notes |
|---|---|---|---|
| FR-001 | Sí | T006, T010 | Tareas previstas; ejecución en implement. |
| FR-002 | Sí | T006, T010 | Tareas previstas; ejecución en implement. |
| FR-003 | Sí | T007, T011, T079 | Tareas previstas; ejecución en implement. |
| FR-004 | Sí | T013, T015, T022, T080 | Tareas previstas; ejecución en implement. |
| FR-005 | Sí | T013, T020, T047, T078 | Tareas previstas; ejecución en implement. |
| FR-006 | Sí | T014, T015, T020 | Tareas previstas; ejecución en implement. |
| FR-007 | Sí | T013, T022 | Tareas previstas; ejecución en implement. |
| FR-008 | Sí | T060, T062, T063 | Tareas previstas; ejecución en implement. |
| FR-009 | Sí | T060, T063, T064 | Tareas previstas; ejecución en implement. |
| FR-010 | Sí | T060, T062, T064 | Tareas previstas; ejecución en implement. |
| FR-011 | Sí | T060, T063, T064 | Tareas previstas; ejecución en implement. |
| FR-012 | Sí | T028, T031, T035, T039, T041 | Cobertura completa: aviso general y desconocidas definidos (U1 resuelto). |
| FR-013 | Sí | T028, T033, T041, T055 | Tareas previstas; ejecución en implement. |
| FR-014 | Sí | T028, T033, T035 | Tareas previstas; ejecución en implement. |
| FR-015 | Sí | T029, T035, T036, T077 | Tareas previstas; ejecución en implement. |
| FR-016 | Sí | T045, T046, T047, T048, T049, T050, T051, T053, T057 | Modalidades de intención coherentes (I1 resuelto). |
| FR-017 | Sí | T029, T032, T034, T039, T040, T046, T052, T056 | Históricos false/legacy ausente/null rechazado definidos (I2 resuelto). |
| FR-018 | Sí | T034, T045, T049, T050, T053 | Tareas previstas; ejecución en implement. |
| FR-019 | Sí | T046, T050, T052, T053, T056, T057 | Tareas previstas; ejecución en implement. |
| FR-020 | Sí | T046, T053, T054, T055, T056 | Tareas previstas; ejecución en implement. |
| FR-021 | Sí | T066, T067, T068, T069, T070, T071, T072 | Tareas previstas; ejecución en implement. |
| FR-022 | Sí | T066, T067, T068, T071, T072 | Tareas previstas; ejecución en implement. |
| FR-023 | Sí | T035, T054, T055, T057, T072 | Tareas previstas; ejecución en implement. |
| FR-024 | Sí | T006, T014, T020, T029, T036, T037, T038, T045, T046, T048, T051, T052, T054, T055, T057, T067, T069, T078 | Tareas previstas; ejecución en implement. |
| FR-025 | Sí | T073, T080 | Tareas previstas; ejecución en implement. |
| FR-026 | Sí | T001, T003, T031, T035, T064, T068, T075, T080 | Tareas previstas; ejecución en implement. |
| FR-027 | Sí | T001, T037, T042, T059, T077, T078, T081 | Tareas previstas; ejecución en implement. |
| FR-028 | Sí | T003, T075, T076, T081 | Tareas previstas; ejecución en implement. |
| SC-001 | Sí | T007, T012, T079 | Tareas previstas; ejecución en implement. |
| SC-002 | Sí | T013, T026, T027, T078 | Tareas previstas; ejecución en implement. |
| SC-003 | Sí | T002, T061, T065 | Tareas previstas; ejecución en implement. |
| SC-004 | Sí | T002, T030, T042, T043, T079 | Tareas previstas; ejecución en implement. |
| SC-005 | Sí | T002, T030, T033, T042, T043 | Medición de jitter/IoU/lag pendiente de implementación. |
| SC-006 | Sí | T030, T077 | Medición completa pareada y RSS pendiente. |
| SC-007 | Sí | T058, T059 | Tareas previstas; ejecución en implement. |
| SC-008 | Sí | T058, T074 | Tareas previstas; ejecución en implement. |
| SC-009 | Sí | T001, T003, T012, T026, T038, T043, T058, T065, T074, T075, T076, T081 | Pendientes006/007 independientes. |
| SC-010 | Sí | T044, T073, T074, T081, T082 | Propuesta de inspección pausada, sin contornos clicables implementados. |

## Constitution Alignment Issues

Ninguno. Se conservan los5 principios:

| Principio | Correspondencia |
|---|---|
| I: modularidad/contratos | Gateway ligero, servicios, helpers puros y cliente compatible; T004/T017/T022/T075. |
| II: validación/trazabilidad | Guardas antes de cuerpo/cola, límites/errores seguros y desenlace efectivo; T014/T019–T020/T029/T037. |
| III: seguridad/retención | Secretos server-only, ingreso local/privado autorizado, owners/TTL/cleanup sin nueva retención; T013–T026/T038/T051/T078. |
| IV: pruebas/modelo | Pruebas primero y regresiones imagen/video/conteo; raw/modelos/pesos/umbrales/OCR preservados; T003/T028–T030/T060–T061/T075–T076. |
| V: recursos | Sin segunda carga de modelos, buffers/cupos/deadlines acotados y FFmpeg incluido en medición; T019–T021/T036–T042/T077. |

No se requieren excepciones constitucionales ni se interpreta Origin/cookie como autenticación de un ingreso público. Los PASS del plan siguen siendo de diseño.

## Unmapped Tasks

Ninguna sin propósito semántico. Los arneses T004/T005 se asocian a FR-028/principioIV y las tareas de componentes a su historia, aunque no repitan un FR explícito. Setup5, US1=7, US2=15, US4=17, US5=15, US3=6, US6=9 y cierre8 suman82. Las6historias conservan sus27escenarios y sus pruebas independientes; el MVP permanece T001–T012.

## Metrics

| Métrica | Resultado |
|---|---:|
| Requisitos funcionales / criterios de éxito | 28 / 10 |
| Requisitos con tareas | 38/38 (100%) |
| Cobertura parcial / requisitos sin tareas | 0 / 0 |
| Tareas / paralelizables | 82 / 29 |
| Historias / escenarios | 6 / 27 |
| CRITICAL / HIGH / MEDIUM / LOW abiertos | 0 / 0 / 0 / 0 |
| Inconsistencias / subespecificaciones / ambigüedades abiertas | 0 / 0 / 0 |
| Duplicaciones accionables | 0 |
| Hallazgos anteriores resueltos | 3 |
| PTS | 439 (plan439, agregados0, eliminados0) |

## Verificación ejecutada

- Hook before_analyze de metricas ejecutado y prerrequisitos resueltos una vez para esta repetición en checkout principal. No hay hook after_analyze registrado.
- JSON Schema2020-12 con jsonschema4.23.0/FormatChecker, mediante uv --isolated --no-project:16 definiciones,13 ejemplos válidos aceptados y9 inválidos rechazados. Entorno separado de las dependencias del proyecto. La caché offline no contenía el paquete; se obtuvo la versión fijada y se ejecutó la validación aislada.
- Casos dirigidos de I2: histórico false aceptado; ausencia legacy sin processing_phase aceptada; null explícito rechazado; respuesta008 con processing_phase y flag ausente rechazada; ready con false rechazado.
- Revisión cruzada de obligatoriedad/opcionalidad de headers y de las instrucciones exactas de leyenda/escenas mixtas. Son verificaciones de contratos/documentos; los tests HTTP/componentes previstos siguen pendientes.
- T001–T082 únicos/consecutivos, rutas/etiquetas/checkboxes válidos, dependencias solo hacia tareas anteriores y sin ciclos; ejemplos [P] mantienen exclusión de archivos compartidos.
- 43 enlaces locales comprobados en12 documentos de diseño (excluido este informe):0 rotos. Los28FR/10SC conservan tareas responsables.
- puntos-tarea.csv regenerado desde tasks.md:82 filas con clasificación agente; se conservaron todas las columnas previas salvo las8 descripciones corregidas, sin nuevos IDs ni volatilidad. T029/T032/T039/T040/T041/T047/T051/T075 quedaron sincronizadas;439PTS.
- Revisión de diff/huellas e índice para conservar cambios ajenos. El commit de esta etapa incluye únicamente la documentación008 corregida y su CSV asociado.

No se ejecutaron inferencias, OCR, pytest/Vitest/Playwright, build de producto ni benchmarks. No corresponden a estas correcciones documentales. Los resultados SC-003/004/005/006 y demás gates deberán demostrarse al implementar; tampoco se cierran006/T067–T068 ni007/T061–T064/T070.

## Next Actions

Se puede iniciar implementación con el plan/tareas corregidos; no quedan remediaciones pendientes de este análisis. Mantener el orden de fases, pruebas pertinentes e incrementos con commit, y dejar abierta cualquier aceptación cuyo gate no se ejecute o falle.

~~~text
$speckit-implement SPECIFY_FEATURE_DIRECTORY=specs/008-exploracion-imagen-video implementa en el checkout principal, conserva la rama feature/008-exploracion-imagen-video y los cambios existentes, ejecuta las pruebas y haz commit de esta etapa.
~~~
