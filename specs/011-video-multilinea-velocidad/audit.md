# Auditoría de implementación011

Entrega en el checkout principal, rama `feature/011-video-multilinea-velocidad`. Modelo, umbral, hilos, intervalo y entorno privado conservados;45CSV preexistentes no incorporados. No hubo comparación larga ni contacto con participantes.

## Commits de producto

```
4c07221 fix(video): preserve independent drafts and fit the fullscreen scene
43e1bf5 feat(frontend): add multiline counters and source-time playback speed
cf6adce feat(video): count independent named lines with bounded historical reduction
```

## Trazabilidad

| Requisito/criterio | Tareas | Evidencia |
| --- | --- | --- |
| FR-001 | T010, T015, T016, T019, T020, T021, T025, T026, T072 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| FR-002 | T015, T016, T019, T020, T021, T023, T025 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| FR-003 | T017, T023, T024, T025, T026 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| FR-004 | T017, T024, T026 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| FR-005 | T003, T016, T018, T023, T026, T041, T044, T047 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| FR-006 | T016, T018, T023, T040, T041, T044, T047 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| FR-007 | T016, T019, T041, T044, T047 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| FR-008 | T040, T042, T043, T045, T046, T047 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| FR-009 | T024, T038, T040, T042, T043, T045, T046, T047 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| FR-010 | T024, T027, T031, T038, T039, T045 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| FR-011 | T027, T028, T031, T032, T039 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| FR-012 | T027, T028, T029, T030, T031, T032, T034, T037, T038, T039, T043 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| FR-013 | T002, T027, T031, T032, T038, T039, T067 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| FR-014 | T015, T016, T019, T020, T028, T029, T032, T033, T034, T039 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| FR-015 | T015, T016, T017, T019, T020, T023, T024, T025, T026, T028, T041, T044 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| FR-016 | T029, T030, T034, T035, T036, T037, T038, T039, T040, T043, T063 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| FR-017 | T048, T049, T051, T052, T053, T054, T056, T064, T072 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| FR-018 | T048, T049, T050, T051, T052, T053, T054, T055, T056 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| FR-019 | T048, T049, T050, T051, T053, T054, T055, T056, T072 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| FR-020 | T030, T035, T037, T048, T050, T051, T053, T054, T055, T056 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| FR-021 | T057, T058, T059, T060, T061, T062, T063, T064, T065, T072 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| FR-022 | T057, T059, T060, T061, T062, T063, T065, T072 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| FR-023 | T040, T042, T043, T045, T046, T047, T049, T052, T054, T070 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| FR-024 | T014, T020, T021, T022, T028, T032, T033, T036, T057, T058, T059, T060, T061, T062, T063, T064, T065, T066, T072 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| FR-025 | T033, T038, T045, T050, T053, T054, T055, T067, T070, T072, T073, T075 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| FR-026 | T015, T016, T019, T020, T021, T022, T023, T025, T028, T030, T032, T035, T037, T040, T041, T044, T057, T058, T059, T060, T062, T063, T064, T065, T066, T073 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| SC-001 | T010, T015, T016, T017, T018, T019, T020, T023, T024, T025, T026, T028, T032, T041, T070, T073, T074 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| SC-002 | T002, T004, T027, T028, T029, T031, T032, T034, T038, T039, T070, T073 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| SC-003 | T027, T029, T030, T034, T035, T036, T037, T038, T039, T050, T053, T055, T056, T070, T073 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| SC-004 | T004, T048, T049, T050, T051, T052, T053, T054, T055, T056, T070, T073 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| SC-005 | T004, T030, T035, T037, T048, T050, T051, T053, T054, T055, T056, T070, T073 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| SC-006 | T004, T017, T024, T026, T040, T042, T043, T045, T046, T047, T049, T052, T054, T070, T073 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| SC-007 | T016, T018, T019, T040, T041, T043, T044, T047, T070, T073 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| SC-008 | T020, T023, T025, T029, T030, T034, T035, T036, T039, T057, T058, T059, T060, T061, T062, T063, T064, T065, T066, T070, T073, T074 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |
| SC-009 | T071, T073, T075 | Pendiente externo: human-validation.md |
| SC-010 | T001, T002, T004, T028, T032, T033, T037, T038, T045, T050, T053, T054, T055, T064, T067, T068, T069, T070, T072, T073, T074, T075 | Verificado técnicamente: pruebas, navegador y contratos; evidence/ |

## Correspondencia de módulos

`CountLineBar.tsx` contiene las tarjetas; `CountLineEditor.tsx` organiza borradores y reutiliza el editor geométrico `ProgressiveCountTools.tsx`. `useCountLines.ts` confirma colecciones e importación; `useCountSnapshots.ts` controla una consulta agregada y `countProjection.ts` aplica intervalos exactos. Las pruebas agrupan matrices relacionadas en los archivos de fixtures/contratos/mutaciones; no se modificaron los contratos010.

El harness se capturó antes de app y la referencia es inmutable. Los JSON de primeras pasadas conservan fallos y motivos de corrección. La salida de timing del navegador se transcribió a `playback-rate.json` antes de que una ejecución posterior limpiara su directorio temporal. Las capturas son sintéticas, sin medios privados.

T071 continúa sin marcar. No se usa E2E para acreditar SC-009 ni para cerrar pendientes humanos/largos de otras iteraciones.


## Cierre de correcciones de convergencia —2026-11-26

La tabla anterior conserva la trazabilidad inicial; los casos omitidos de la revisión de Phase9 se completan con T076–T085. Estado actual84/85, pendiente externo exclusivo T071/SC-009. Pruebas y límites actuales: [validation.md](validation.md) y [evidence/convergence-corrections.json](evidence/convergence-corrections.json). No se cierran gates humanos/largos anteriores.

| Tarea | Requisito / corrección | Evidencia ejecutada |
| --- | --- | --- |
| T076 | FR-003/014/015/026: operación seleccionada aislada | countLineDrafts: aplicar/borrar A conserva B confirmado y su propuesta |
| T077 | FR-007/021/026: geometría remota coherente | countLineDrafts: puntos remotos y metadatos durante edición |
| T078 | FR-021/026: recuperación sin duplicar ni retirar contexto nuevo | countLineRecovery: fallo inicial/posterior, cancelación y autoridad |
| T079 | FR-014/026: error solo de línea/revisión afectada | cinco casos en test_count_lines_reduction.py y suite completa562 |
| T080 | FR-015/026: propuestas preservadas y conflicto explícito | countLineDrafts y playbackRateIntegration: base remota y borrador inicial distinto |
| T081 | FR-003/015: borrador vacío no reaparece | countLineDrafts: borrar A nueva, añadir/aplicar B |
| T082 | FR-021/026: importación de contexto correcto | countLineRecovery: trabajo/generación ajenos y respuesta tardía |
| T083 | FR-001: límite acumulado anunciado | countLineDrafts:128/128; countLineRecovery: carrera de admisión |
| T084 | FR-018/019/020/025: pruebas funcionales de reloj/decoder/cachés | playbackRateIntegration, sourceDecoder, frameCache y21casos Chromium |
| T085 | FR-005: nombre inicial único normalizado | countLineDrafts: caja, espacios, NFC/NFD y reservas confirmadas |

Commits de producto de esta corrección: `45df949` (backend/T079) y `9273112` (frontend y regresiones T076–T078/T080–T085). Después del ajuste final de nombres/colores se repitió configuración de diez líneas:3/3aprobadas en1440/768/360px. Los21escenarios y estas3revalidaciones se registran por separado; no se suman como24casos distintos.
