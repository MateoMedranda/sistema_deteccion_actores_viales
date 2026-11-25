# Validación documental de 011 — 2026-11-25

Se crea desde main, commit base e0b88f3, en el checkout principal y rama nueva feature/011-video-multilinea-velocidad. Se conservan los 45 archivos de sesiones previos sin incorporarlos a los commits de esta etapa. El turno anterior solo abrió una sesión metodológica: no modificó producto; la solicitud de retirar sentido/flecha se incorpora aquí, sin afirmar que esté implementada.

Plantilla resuelta: spec-template de core, mediante `specify preset resolve spec-template`. Constitución 1.0.0 consultada: modularidad, validación, seguridad, pruebas y medición de rendimiento aplican al plan posterior. No hay excepción constitucional ni cambio de modelo autorizado.

Cinco historias priorizadas,26 requisitos funcionales,10 criterios de éxito, entidades, casos límite y supuestos. Checklist 16/16 conforme tras revisión. No hay aclaraciones pendientes.

Trazabilidad documental:

| Historia | Requisitos principales | Criterios |
| --- | --- | --- |
| US1: configurar líneas | FR-001–005,014–015 | SC-001,006,009 |
| US2: cruces por línea | FR-010–016 | SC-002–003,008 |
| US3: tarjetas y colores | FR-006–009,023 | SC-006–007,009 |
| US4: velocidad | FR-017–020 | SC-003–005,009–010 |
| US5: recuperar contexto | FR-021–022,024–026 | SC-008,010 |

Los contratos y decisiones de almacenamiento permanecen pendientes de plan. Capacidad mínima 10 y presets 0,25× a 2× son supuestos verificables; no promesas de escalabilidad ilimitada ni de acelerar inferencia. El conteo es una vez por identidad local y línea/revisión, no conteo de rutas ni suma global sin duplicados entre accesos.

Solo se validan documentos en esta etapa: no se ejecuta la suite de producto, comparación larga ni validación humana. Las pruebas de implementación y de uso quedan para sus fases correspondientes.

Hooks: before_specify de metricas obligatorio ejecutado; no hay hooks after_specify registrados. Registro de sesión de especificación separado de la sesión interrumpida sin cambios confirmados.
