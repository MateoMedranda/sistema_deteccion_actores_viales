# Correcciones autorizadas del análisis — 2026-11-24

Rama: feature/010-video-detalle-conteo, checkout principal. Se corrigen A1/U1 de severidad media; no se modifica código de producto ni se ejecutan pruebas de implementación.

| Hallazgo | Corrección | Trazabilidad |
|---|---|---|
| A1: clases elegibles para cruces sin definir | Clase medida normalizada al confirmar; lista vehicular explícita con bicicletas/motos, exclusión de personas y clases no catalogadas. Todas las mediciones actualizan geometría; una exclusión no consume un cruce futuro válido. Evento con class_key_at_crossing inmutable, independiente de votos/OCR posteriores. El inventario conserva desconocidos para revisión. | FR-010, SC-004; T005, T034–T035, T037–T038, T045, T051; spec, plan, research, data-model y contratos. |
| U1: prueba de rendimiento sin tarea de creación ni referencia previa | T001 crea harness sintético autocontenido y captura referencia antes de modificar producto. Calentamiento y al menos tres medidas, medianas, entorno/fixture/parámetros y huellas. Captura única, comparación T071 sin sobrescritura ni recaptura del candidato como base; referencia inválida deja validación pendiente/fallida. | T001 → T002; T071 depende de T001 y T070. Plan, research y quickstart describen el protocolo. |

## Controles documentales

74 tareas pendientes, IDs consecutivos, dependencias anteriores y sin ciclos; 12 marcadores de paralelismo. Cobertura explícita: 24/24 requisitos funcionales y 9/9 criterios de éxito. Se validan los 16 esquemas, 8 ejemplos positivos y 13 operaciones del contrato. La trazabilidad completa permanece en task-generation.md.

Se recalculan 402 PTS: T001 pasa de documentación/baja (1) a prueba/alta (4), porque ahora produce el harness y la referencia. Se conservan las 74 tareas, su origen plan y el registro histórico inicial de 399 PTS; no son horas ni FPS. No quedan clasificaciones heurísticas pendientes.

## Límites y siguiente etapa

La referencia publication-baseline.json y la comparación publication-overhead.json son entregables futuros de T001/T071: no existen como evidencia de esta revisión. No se ejecutan modelos, comparación larga ni validaciones humanas previamente diferidas. El análisis posterior vuelve a revisar los artefactos en modo de solo lectura; estas correcciones no acreditan implementación ni convergencia del producto.
