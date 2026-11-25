# Validación de generación de tareas — Iteración 010

Fecha: 2026-11-24. Etapa: speckit-tasks. Resultado: tareas listas para análisis cruzado; implementación no iniciada.

## Documentos y reglas utilizados

spec.md, plan.md, research.md, data-model.md, contracts/, quickstart.md y constitución1.0.0. Plantilla tasks-template resuelta por setup-tasks.ps1. Se conserva la organización por historia y se incluyen pruebas por los escenarios/criterios de la especificación, el plan aprobado y el principio IV de la constitución.

No se modificaron spec.md, plan.md, research.md, data-model.md ni contratos. Los módulos auxiliares de acceso, store, worker y hooks concretan la separación modular del plan; no añaden capacidades ni cambian decisiones de producto. No se ejecutaron pruebas de producto, inferencia, migraciones ni benchmark para generar tareas.

## Resultado estructural

| Grupo | IDs | Cantidad |
|---|---|---:|
| Setup | T001–T003 | 3 |
| Fundamentos | T004–T008 | 5 |
| US1 ficha consistente | T009–T015 | 7 |
| US2 inspección temporal | T016–T033 | 18 |
| US3 conteo dirigido | T034–T047 | 14 |
| US4 resumen por clase | T048–T058 | 11 |
| US5 exportación etiquetada | T059–T068 | 10 |
| Cierre transversal | T069–T074 | 6 |
| Total | T001–T074 | 74 |

Comprobaciones realizadas:74 IDs consecutivos/únicos;74 casillas pendientes; formato obligatorio y ruta concreta en cada descripción; etiqueta US solo en fases de historia;8 fases con objetivo y checkpoint; dependencias a tareas anteriores (grafo sin ciclos);12 marcas P, con archivos distintos en cada ola de ejemplo;24 FR y9 SC cubiertos; restricciones del modelo de datos citadas literalmente en las tareas de DTO/datos responsables. No quedan placeholders ni se marcaron tareas como realizadas.

Pruebas por historia se escriben antes de la implementación correspondiente; las tareas de verificación posteriores ejecutan esas pruebas y registran resultados. Cambios compartidos de main/lifespan/proxy/store/reproductor se serializan aunque el backend de distintas historias pueda comprobarse aisladamente.

MVP recomendado: Setup+Fundamentos+US1 (T001–T015), que entrega la ficha visual consistente sobre datos actuales. No debe presentarse como resolución del contexto temporal ni de las otras historias hasta completar sus tareas.

## Hook obligatorio de puntos SDD

before_tasks: sesión de métricas registrada. after_tasks: puntos.ps1 ejecutado; se revisaron las74 clasificaciones heurísticas por su entregable y complejidad, se modificaron únicamente tipo/complejidad/clasificado_por y se recalculó con el script oficial. Resultado: **399 PTS**, todos de origen plan;0 agregados,0 eliminados,0 filas heurísticas pendientes. Los pesos SDD son hipótesis metodológicas del proyecto;399 PTS no representan399 horas, un presupuesto ni FPS.

## Trazabilidad de requisitos

| Requisito | Tareas |
|---|---|
| FR-001 | T009, T010, T011, T012, T013, T014, T015, T025, T029, T031, T032, T072 |
| FR-002 | T009, T010, T011, T013, T014, T015 |
| FR-003 | T009, T010, T011, T012, T013, T014, T015, T031, T032, T036, T043, T045, T046, T055, T056, T072 |
| FR-004 | T016, T017, T018, T019, T021, T022, T023, T024, T026, T028, T029, T030, T031, T032, T033 |
| FR-005 | T016, T017, T018, T019, T022, T023, T024, T026, T028, T029, T030, T031, T032, T033 |
| FR-006 | T016, T017, T018, T019, T021, T024, T025, T026, T028, T029, T030, T031, T032, T033 |
| FR-007 | T016, T017, T018, T019, T021, T024, T026, T028, T029, T030, T031, T032, T033 |
| FR-008 | T016, T017, T018, T019, T020, T021, T023, T024, T025, T026, T027, T028, T029, T030, T031, T032, T033 |
| FR-009 | T034, T036, T037, T041, T042, T043, T045, T046, T047 |
| FR-010 | T034, T035, T037, T038, T041, T046, T047 |
| FR-011 | T034, T035, T037, T038, T041, T046, T047 |
| FR-012 | T034, T035, T037, T038, T039, T040, T041, T044, T045, T046, T047 |
| FR-013 | T034, T036, T038, T040, T041, T044, T045, T046, T047 |
| FR-014 | T035, T036, T037, T038, T039, T040, T041, T044, T045, T046, T047 |
| FR-015 | T035, T036, T037, T039, T040, T041, T042, T043, T044, T045, T046, T047 |
| FR-016 | T048, T049, T050, T051, T052, T053, T054, T055, T056, T057, T058, T071 |
| FR-017 | T048, T049, T050, T051, T052, T053, T054, T055, T056, T057, T058, T071 |
| FR-018 | T007, T048, T049, T050, T051, T052, T053, T054, T055, T056, T057, T058 |
| FR-019 | T059, T060, T061, T062, T063, T064, T065, T066, T067, T068 |
| FR-020 | T059, T060, T061, T062, T064, T065, T067, T068 |
| FR-021 | T059, T060, T062, T063, T064, T065, T066, T067, T068 |
| FR-022 | T005, T006, T007, T008, T012, T022, T027, T030, T033, T039, T041, T047, T049, T052, T053, T054, T057, T058, T060, T061, T063, T064, T065, T066, T067, T068, T069, T070, T071, T072 |
| FR-023 | T005, T006, T007, T008, T016, T017, T019, T020, T021, T023, T024, T025, T026, T027, T032, T033, T035, T037, T039, T041, T047, T049, T050, T053, T054, T058, T060, T063, T064, T065, T066, T067, T068, T069, T070, T072 |
| FR-024 | T001, T008, T015, T027, T033, T047, T058, T068, T070, T071, T072, T073, T074 |

## Trazabilidad de criterios de éxito

| Criterio | Tareas con verificación |
|---|---|
| SC-001 | T009, T010, T014, T015, T072 |
| SC-002 | T016, T017, T018, T028, T031, T032, T033, T072 |
| SC-003 | T016, T017, T018, T028, T031, T032, T033, T072 |
| SC-004 | T034, T035, T038, T040, T046, T047, T072 |
| SC-005 | T035, T036, T040, T045, T046, T047, T072 |
| SC-006 | T048, T049, T051, T052, T055, T056, T057, T058, T072 |
| SC-007 | T059, T060, T062, T064, T067, T068, T072 |
| SC-008 | T017, T033, T035, T047, T049, T052, T057, T058, T059, T060, T064, T066, T067, T068, T070, T071, T072 |
| SC-009 | T009, T010, T014, T015, T031, T032, T036, T042, T043, T045, T046, T047, T056, T057, T072 |

## Conservación y siguiente fase

Rama feature/010-video-detalle-conteo conservada en checkout principal. Archivos no versionados anteriores de otras sesiones no se añaden al commit de esta etapa. Código backend/frontend y .env privados intactos; los CSV de puntos son documentación metodológica. Siguiente paso: speckit-analyze para contrastar especificación, plan y tareas antes de implementar. Los pendientes largos/humanos de009 siguen pendientes.
