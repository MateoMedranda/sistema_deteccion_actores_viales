# Generación y validación de tareas011 —2026-11-25

Checkout principal, rama feature/011-video-multilinea-velocidad y base cd01544. Se conserva el trabajo previo; solo se añaden tareas, PTS, validación y registro documental. No se implementa producto, ejecutan tests futuros ni se modifica .env/modelo/cadencia/hilos.

## Entradas y estructura

setup-tasks resuelve FEATURE_DIR absoluto y tasks-template de core con TASKS_TEMPLATE_CONTENT. Se revisan spec/plan, investigación, modelo de datos, contratos/UI/esquemas/ejemplos, quickstart y constitución1.0.0. Pruebas incluidas porque la especificación exige escenarios/criterios verificables y regresiones, no por inferencia de palabras clave.

75 tareas pendientes en ocho fases: Setup4, Foundation10, US1=12, US2=13, US3=8, US4=9, US5=9 y cierre10. Todas usan checkbox pendiente, ID secuencial, path exacto y story en las cinco fases de historia. Cada historia incluye prueba independiente y casos antes del comportamiento nuevo; se conservan pruebas anteriores que ya pasan.

## Dependencias y paralelismo

144 aristas explícitas, todas hacia IDs anteriores, sin ciclos; gate T014 agrupa los14 prerrequisitos. La referencia T001 precede las modificaciones de dependencias/app.23 tareas [P] tienen al menos una pareja de archivos diferentes con dependencias compatibles; los ejemplos por historia no autorizan escrituras simultáneas sobre módulos compartidos ni lanzamiento de agentes por sí solos.

US1 configura líneas con controles de nombre y selección en el editor, sin esperar a US3; configura y persiste, sin acreditar conteo aún. MVP operativo recomendado agrega US2/US3 y sus tarjetas/cruces bidireccionales. US4 tiene reloj/control aislados, pero su integración en el mismo player se serializa. US5 conserva contratos previos y recuperación/importación.

T071requiere cinco personas: si no se realiza, permanece pendiente. T075cierra el código/documentación técnica sin depender de T071 y debe declarar esa validación pendiente, sin afirmar75/75 ni aprobar SC-009. No se amplía el alcance a la comparación larga ni se cierran pendientes anteriores.

## Restricciones preservadas

Se verifican17 citas literales contra el diseño: SafeInt/UUID/tiempos,32objetos, coordenadas/extremos, grafemas/bytes/codepoints, NFC/casefold, RGB, clave compuesta, semántica de omisión/reordenación/metadata, geometría inclusiva/tolerancias, null/ready/validez exclusiva e import marker. DTOs deben respetar todos los required/enum/nullables/facets de los11 esquemas; sus casos positivos/negativos y semánticos se convierten en pruebas de producto, no se dan por aprobados por JSON Schema.

Se traza valid_until_us como regla definitiva de cantidades entre cuadros: un poll400ms no exige igualdad con cada cuadro, solo pertenecer al intervalo exacto. Una sola petición agregada en vuelo, demanda coalescida y100msmínimo. Geometría/reducer no repite detección ni bloquea GET; colores/nombres no reinician conteos. Gateway conserva allowlist, cuerpo64KiB, no-store, permisos/CSRF y TTL del padre.

## Puntos de Tarea SDD

Hook before_tasks de sesión ejecutado; after_tasks obligatorio puntos ejecutado. Primera pasada heurística342 PTS, luego revisión de las75 filas por entregable y complejidad, no por vocabulario. Se editan únicamente tipo/complejidad/clasificado_por antes de recalcular con el script oficial. Resultado365 PTS de plan,0 agregados/0 eliminados y0 clasificaciones heurísticas pendientes. Es tamaño relativo del trabajo previsto, no horas ni rendimiento ni pruebas aprobadas.

La validación humana T071produce informe manual y se clasifica como documentación; pruebas automatizadas/benchmarks como prueba. Servicios/algoritmos y protocolos no triviales reciben complejidad alta; DTO, configuración y composición rutinaria conservan su clase por entregable. Las otras columnas/origen siguen bajo el script oficial.

## Cobertura de requisitos

| Requisito | Tareas |
| --- | --- |
| FR-001 | T010, T015, T016, T019, T020, T021, T025, T026, T072 |
| FR-002 | T015, T016, T019, T020, T021, T023, T025 |
| FR-003 | T017, T023, T024, T025, T026 |
| FR-004 | T017, T024, T026 |
| FR-005 | T003, T016, T018, T023, T026, T041, T044, T047 |
| FR-006 | T016, T018, T023, T040, T041, T044, T047 |
| FR-007 | T016, T019, T041, T044, T047 |
| FR-008 | T040, T042, T043, T045, T046, T047 |
| FR-009 | T024, T038, T040, T042, T043, T045, T046, T047 |
| FR-010 | T024, T027, T031, T038, T039, T045 |
| FR-011 | T027, T028, T031, T032, T039 |
| FR-012 | T027, T028, T029, T030, T031, T032, T034, T037, T038, T039, T043 |
| FR-013 | T002, T027, T031, T032, T038, T039, T067 |
| FR-014 | T015, T016, T019, T020, T028, T029, T032, T033, T034, T039 |
| FR-015 | T015, T016, T017, T019, T020, T023, T024, T025, T026, T028, T041, T044 |
| FR-016 | T029, T030, T034, T035, T036, T037, T038, T039, T040, T043, T063 |
| FR-017 | T048, T049, T051, T052, T053, T054, T056, T064, T072 |
| FR-018 | T048, T049, T050, T051, T052, T053, T054, T055, T056 |
| FR-019 | T048, T049, T050, T051, T053, T054, T055, T056, T072 |
| FR-020 | T030, T035, T037, T048, T050, T051, T053, T054, T055, T056 |
| FR-021 | T057, T058, T059, T060, T061, T062, T063, T064, T065, T072 |
| FR-022 | T057, T059, T060, T061, T062, T063, T065, T072 |
| FR-023 | T040, T042, T043, T045, T046, T047, T049, T052, T054, T070 |
| FR-024 | T014, T020, T021, T022, T028, T032, T033, T036, T057, T058, T059, T060, T061, T062, T063, T064, T065, T066, T072 |
| FR-025 | T033, T038, T045, T050, T053, T054, T055, T067, T070, T072, T073, T075 |
| FR-026 | T015, T016, T019, T020, T021, T022, T023, T025, T028, T030, T032, T035, T037, T040, T041, T044, T057, T058, T059, T060, T062, T063, T064, T065, T066, T073 |

## Cobertura de criterios de éxito

| Criterio | Tareas |
| --- | --- |
| SC-001 | T010, T015, T016, T017, T018, T019, T020, T023, T024, T025, T026, T028, T032, T041, T070, T073, T074 |
| SC-002 | T002, T004, T027, T028, T029, T031, T032, T034, T038, T039, T070, T073 |
| SC-003 | T027, T029, T030, T034, T035, T036, T037, T038, T039, T050, T053, T055, T056, T070, T073 |
| SC-004 | T004, T048, T049, T050, T051, T052, T053, T054, T055, T056, T070, T073 |
| SC-005 | T004, T030, T035, T037, T048, T050, T051, T053, T054, T055, T056, T070, T073 |
| SC-006 | T004, T017, T024, T026, T040, T042, T043, T045, T046, T047, T049, T052, T054, T070, T073 |
| SC-007 | T016, T018, T019, T040, T041, T043, T044, T047, T070, T073 |
| SC-008 | T020, T023, T025, T029, T030, T034, T035, T036, T039, T057, T058, T059, T060, T061, T062, T063, T064, T065, T066, T070, T073, T074 |
| SC-009 | T071, T073, T075 |
| SC-010 | T001, T002, T004, T028, T032, T033, T037, T038, T045, T050, T053, T054, T055, T064, T067, T068, T069, T070, T072, T073, T074, T075 |

## Resultado

Formato, cobertura26 FR/10 SC, grafo, paths, citas y PTS comprobados. Resumen de validación en task-generation.json. Las tareas siguen pendientes y no hay cambios de backend/app ni frontend/src en esta etapa. Listo para speckit-analyze; no es una auditoría de implementación.


## Corrección autorizada I1/U1 —2026-11-25

I1: se armonizan data-model§8/§10 y contracts/README para separar el at_us solicitado de la validez posterior durante reproducción ordinaria. El total ready es exacto en [snapshot.at_us,line.valid_until_us); seek/revisión/generación invalidan respuestas de contexto anterior. No se exige un snapshot por cuadro.

U1: T011 se acota a persistencia estructural, reapertura y purge de fixtures sin servicio/rutas. T014 exige solo lo disponible al terminar fundamentos. Descriptor funcional vacío se verifica en T015 y las cuotas/tombstones/admitted_count en T016, satisfechas al implementar US1. No se añaden IDs ni se cambian las dependencias; se revisa y recalcula PTS con el script oficial.

El registro de corrección y la comprobación documental se conservan en [remediation.md](remediation.md). No se implementa código ni se consideran aprobadas pruebas funcionales/humanas por esta enmienda.
