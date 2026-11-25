# Revisión de diseño011 —2026-11-25

Rama real feature/011-video-multilinea-velocidad, checkout principal, base6880055. setup-plan resolvió FEATURE_SPEC/IMPL_PLAN/FEATURE_DIR correctos; su BRANCH omite el prefijo feature/, sin cambiar la rama de Git. Plantilla del plan y constitución1.0.0 consultadas. No se toca producto ni se genera tasks.md.

## Resultado de fases

Investigación realizada por tres agentes de solo lectura y consolidada en research.md: conteo/store/worker, reproductor/editor y contratos/gateway. Se consultaron fuentes primarias para grafemas/reloj; el resto se fundamenta en el checkout existente. Doce decisiones con alternativas y motivos, sin incógnitas bloqueantes. Se define dependencia directa regex que aún no está instalada y deberá fijarse en lock al implementar, sin afirmar que ya se incorporó.

Constitution Check previo PASS: modularidad, validación, privacidad, pruebas y medición previstas sin excepción. Revisión posterior PASS documental: contratos aditivos, GET sin efectos, presupuesto/limpieza/TTL, esquema de reloj y estrategia de pruebas satisfacen los principios. No son gates de ejecución aprobados.

## Contratos y ejemplos comprobados

-11 definiciones JSON Schema2020-12 válidas;15 referencias internas/externas resueltas;4 operaciones OpenAPI con identificadores distintos y autenticación declarada.
-9 ejemplos positivos aceptados por sus esquemas;12 ejemplos estructurales negativos rechazados. Los10 ejemplos semánticos negativos pasan deliberadamente la forma y están revisados contra invariantes de data-model/README; su rechazo por servicio/parser queda pendiente de implementación. No confundir JSON Schema con validación completa de negocio.
-32 colores iniciales distintos,6 enlaces documentales locales existentes y sin placeholders de plantilla ni aclaraciones pendientes en artefactos de diseño. Resultado agregado en design-validation.json.
- YAML de extensiones parseado; hook obligatorio before_plan de métricas ejecutado antes de setup. Sin hooks after_plan registrados.

## Hallazgo de revisión y resolución

La primera versión exigía que cada respuesta de conteo coincidiera con el cuadro actual pese al poll400ms, lo que dejaría las tarjetas actualizando durante reproducción30cuadros/s. Se corrige el diseño con valid_until_us exclusivo por línea: mínimo del siguiente evento estrictamente posterior, cobertura y prefijo. El número es exacto dentro de [snapshot.at_us,valid_until_us), sin anticipar ni retrasar cruces; se consulta al agotar intervalo mediante demanda coalescida, con una petición en vuelo y separación mínima100ms. Respuestas de otro seek/revisión/generación siguen descartadas. Se añade admitted_count al descriptor para explicar cuotas incluyendo IDs eliminados.

## Trazabilidad para generación de tareas

| Requisitos | Diseño | Validación futura |
| --- | --- | --- |
| FR-001–004 | colección UUID, capacidades y editor selectivo |1/10 líneas; pointer/touch/teclado; selección de superpuestas |
| FR-005–007 | grafemas/NFC/casefold, RGB único; metadatos sin reset | nombres1/60/61, acentos, duplicados, swap atómico de color/nombre |
| FR-008–009 | CounterBar dentro del root fullscreen | tarjetas nombradas, foco y escena libre de overlay |
| FR-010–013 | finite-center-both-v1 y catálogo actual | seis clases, dos sentidos, contacto/extremos/prolongación, identidad repetida/multilínea |
| FR-014–016 | CAS/revisión geométrica, reducer justo, intervalos exactos | cambio de una línea, cobertura/validez exclusiva,10 seeks, atraso sin cantidades futuras |
| FR-017–020 | reloj puro, presets y admisión existente |0,5/1/2×; pausa/espera;20 intentos futuros; no reinicio de decoder/modelos |
| FR-021–022 | persistencia temporal/importación única/tombstones | reinicio/recarga, importación/borrado/reintento, ausencia de procedencia |
| FR-023–024 | layout adaptable, parent/CSRF/origen/TTL |360/768/1440, fullscreen, auth/body/query/purge |
| FR-025–026 | contratos anteriores intactos, rollback/reconciliación | imagen/video/inspección/exportación y respuestas tardías |

SC-001/002/003/005/006/007/008 se cubren con escenas/contratos/UX; SC-004 con reloj y medición de30s completos; SC-009 con cinco personas; SC-010 con regresiones y benchmark breve0/1/10 líneas. Los umbrales de desempeño son objetivos iniciales, no resultados de este plan.

## Límites y pendientes

Sin pruebas de producto ni mediciones de FPS, latencia real o evaluación humana ejecutadas durante plan. La primera tarea deberá capturar la referencia sintética011 antes de editar producto; no se reemplazan las referencias010. Comparación larga/modelos reales y gates humanos anteriores conservan estado pendiente. El plan no cambia pesos/umbrales/hilos/intervalo/.env ni autoriza nuevos datos de reconocimiento. Los45 CSV previos sin seguimiento se conservan fuera de los commits.

Listo para speckit-tasks; no comenzar implementación sin las fases siguientes.
