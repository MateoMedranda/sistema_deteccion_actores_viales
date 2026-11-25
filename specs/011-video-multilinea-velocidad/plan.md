# Implementation Plan: Velocidad y líneas de conteo con nombre

**Branch**: `feature/011-video-multilinea-velocidad` | **Date**: 2026-11-25 | **Spec**: [spec.md](spec.md)

**Input**: `specs/011-video-multilinea-velocidad/spec.md`, 26 FR / 10 SC. Checkout principal; base documental6880055. La ruta de feature resuelta por setup-plan es correcta; su campo BRANCH omite el prefijo, por lo que se usa la rama real verificada con Git.

## Summary

Añadir un reloj de reproducción0,25×–2× al visor canvas existente y una colección durable de líneas independientes, con nombre/color editable desde tarjetas situadas por encima del video. Cada segmento contará cruces reales en ambos sentidos, una sola vez por identidad local/revisión. La reproducción sigue limitada al prefijo confirmado y consulta cantidades del cuadro pintado, no del tiempo futuro del reloj.

La experiencia nueva usa contratos propios `video-count-lines-v1` y conserva los contratos cerrados de009/010 y su comportamiento direccional para consumidores anteriores. No modifica detección, pesos, hilos, enriquecimiento, exportaciones ni configuración privada. La implementación futura sí necesita cambios coordinados de backend, gateway y frontend. Esta entrega termina en diseño; no crea tasks.md ni implementa capacidades.

## Technical Context

**Language/Version**: Python 3.12 (entorno local 3.12.15) y TypeScript 5.6; React 18.3/Vite 5.4 existentes. Mantener backend/ y frontend/ separados, Speckit/documentación en raíz.

**Primary Dependencies**: FastAPI/Pydantic 2, SQLite de la biblioteca estándar, PyAV 19.0.2, WebCodecs/MP4Box y reloj RAF existentes. Planificar dependencia directa `regex>=2025,<2027` y fijarla en backend/uv.lock durante implementación para grafemas; no está instalada actualmente. `Intl.Segmenter` ofrece feedback local cuando existe, con servidor como autoridad y sin fallback inseguro a string.length. No se instala nada en plan.

**Storage**: Nuevas tablas p_count_lines_* en la misma base/conexión/lock de ProgressiveStore. Solo configuración, estados y eventos temporales del trabajo; sin nuevos videos/recortes. Revisiones actuales, tombstones de IDs y marcador de importación comparten TTL del padre. Velocidad solo en memoria del cliente.

**Testing**: pytest unitario/integración/contratos y benchmark sintético; Vitest para reloj, editor, estados y cliente; Playwright con API/gateway/Vite aislados y escena011 nueva multiclase/bidireccional. Esquemas JSON Schema2020-12 y OpenAPI3.1 documentales. Sin comparación larga con modelos reales en esta etapa.

**Target Platform**: Servicio Python 3.12 y navegadores actuales capaces de la reproducción progresiva existente; escritorio/tablet/móvil a1440/768/360px. Mantener explicación de incompatibilidad de WebCodecs. No se amplía el soporte de códecs ni se promete tiempo real en edge.

**Project Type**: Aplicación web con servicio de análisis, gateway de sesión y frontend.

**Performance Goals**: Una consulta agregada de cantidades cada400 ms, sin diez pollers; demanda coalescida por seek o fin de intervalo válido, una sola en vuelo y separación mínima100 ms (≤10 Hz en ráfaga). Reanclaje de reloj sin salto ni nueva decodificación al cambiar velocidad. Objetivos iniciales en fixture sintético300 cuadros×20 observaciones: p95 de sección crítica del reducer≤10 ms y GET agregado≤250 ms, catch-up de10 líneas≤5s; medir y ajustar el tamaño de lote si no se cumple, sin presentar estos objetivos como mediciones obtenidas. Publicación0líneas frente a base: investigar regresión>5%; medir por separado1/10 líneas y sincronización de reproducción, sin confundir con FPS de YOLO.

**Constraints**: GET sin efectos; autorización/generación/TTL antes de leer/publicar; cuerpos64 KiB, respuestas existentes2 MiB; nombres1–60 grafemas y≤2048 bytes UTF-8; colores sólidos RGB únicos;32 líneas como techo del protocolo y10 activas por defecto.128 identidades de línea admitidas por trabajo incluyendo eliminadas. Watermark exclusivo, clases aprobadas y solo mediciones reales. No rescalar PTS, índices de cuadro ni timestamps de identidad del decoder.

**Scale/Scope**: Cinco historias;10 líneas verificadas simultáneamente, configurable10–32 con límites anunciados. Una identidad puede contribuir a varias líneas; no agregar sus tarjetas como vehículos físicos únicos. Línea nueva o desplazada se reconstruye sobre observaciones existentes desde el inicio; color/nombre no reinician cálculo.

## Constitution Check

*GATE previo a investigación: PASS. Revisión posterior al diseño: PASS documental, sujeta a pruebas futuras de implementación.*

| Principio | Antes de investigación | Diseño posterior / evidencia prevista |
| --- | --- | --- |
| I: módulos/contratos | PASS: reusar orquestación separada | Servicio multilínea, ruta fina, contratos nuevos y reloj puro; interfaces en contracts/ |
| II: validación/trazabilidad | PASS: entradas acotadas | Validación semántica, CAS, errores seguros, métricas agregadas sin nombres/rutas/placas |
| III: privacidad | PASS: padre autorizado temporal | Sin nuevos medios; purge/TTL, no-store y protección CSRF/origen existentes |
| IV: pruebas/calidad | PASS: modelo intacto | Escena011 con seis clases, imagen/video, compatibilidad y controles de reproducción; no atribuir estas pruebas al plan |
| V: rendimiento | PASS: sin inferencia nueva | Reducer justo/acotado, lectura agrupada, referencia de escritura única antes de cambios y comparación0/1/10 |

No hay excepción constitucional ni desconocido bloqueante. El análisis de grafemas, migración y compatibilidad queda resuelto en [research.md](research.md). Los gates de producto/humanos anteriores no se cierran por esta revisión.

## Project Structure

### Documentation (this feature)

```text
specs/011-video-multilinea-velocidad/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── design-validation.json
├── design-validation.md
├── checklists/requirements.md
├── specification-validation.md
└── contracts/
    ├── README.md
    ├── schemas.json
    ├── examples.json
    ├── openapi-additions.yaml
    └── ui.md
```

tasks.md será generado por speckit-tasks; no existe como salida de esta fase.

### Source Code (repository root)

```text
backend/
├── app/domain/count_lines.py                      # nuevo: DTO/validación
├── app/services/count_lines_store.py              # nuevo: colección/CAS/purge
├── app/services/count_lines_service.py            # nuevo: configuración/snapshot/import
├── app/services/count_lines_reducer.py            # nuevo: reducción medida por línea
├── app/services/directed_counting.py              # existente: extraer geometría común sin cambiar modo anterior
├── app/services/video_detail_worker.py            # existente: scheduling justo
├── app/services/video_progressive_store.py        # existente: lifecycle
├── app/core/{config,lifespan}.py                  # existente: límites/inyección
├── app/api/routes/video_count_lines.py            # nuevo: cuatro operaciones
├── app/main.py                                   # existente: router/límite de cuerpo
├── app/web/proxy.py                              # existente: allowlist/query/cuerpo
├── tests/{unit,integration,contract,performance,e2e}/
└── scripts/                                      # reporte de comparación breve011
frontend/
├── src/features/video-analysis/
│   ├── playbackClock.ts                          # nuevo: tiempo fuente/rate/anchor
│   ├── countLinesContracts.ts                    # nuevo: DTO/parser cerrados
│   ├── useCountLines.ts                          # nuevo: colección + polling agregado
│   ├── CountLineBar.tsx                          # nuevo: tarjetas/nombre/color/selección
│   ├── PlaybackRateControl.tsx                   # nuevo: selector accesible
│   ├── ProgressiveCountTools.tsx                 # adaptar editor a colección, sin flecha
│   ├── useCountDraft.ts                          # adaptar borradores e inicialización fiable
│   ├── ProgressiveVideoPlayer.tsx                # integrar reloj/líneas/barra
│   └── VideoWorkspace.tsx                        # conservar fotograma inicial/contexto
├── src/styles.css                                # adaptar fullscreen/responsive
├── tests/features/video-analysis/
└── e2e/                                          # escena/pruebas011
```

**Structure Decision**: Ampliación aditiva sobre la estructura actual. No mover archivos del backend/frontend ni crear un nuevo servidor de base de datos. Los paths nuevos son propuestas del diseño, no archivos de producto ya creados.

## Phase 0 — Research

Investigación de repositorio en tres frentes: reducción/vida temporal, reloj/editor y contratos/gateway/pruebas. [research.md](research.md) recoge decisiones, alternativas y fuentes primarias. Se comprueban el reloj canvas, el lock SQLite compartido, las respuestas010 cerradas, el gateway con allowlist y la ausencia de regex. No se cargan modelos ni medios privados.

## Phase 1 — Design & Contracts

### Backend y compatibilidad

Crear colección independiente; no ensanchar Capabilities/DirectedCount de010. Cuatro operaciones nuevas: GET descriptor, PUT colección completa con CAS, GET cantidades en lote por instante y POST importación de línea anterior. Contratos y errores en [contracts/README.md](contracts/README.md), datos en [data-model.md](data-model.md). Mutaciones atómicas con normalización/unicidad/capacidad. UUIDs estables elegidos por cliente, tombstones hasta TTL y reconciliación de respuesta perdida evitan duplicación/reaparición.

Importación explícita e idempotente, disparada por el cliente activo cuando se ofrece una línea anterior y la colección está vacía. Conserva geometría, asigna Línea 1/color y recalcula ambos sentidos. Nunca toma el total direccional antiguo. El marcador impide reimportar una línea eliminada. No tocar p_directed_count_* ni respuestas anteriores.

### Reducción y rendimiento

Extender el worker existente sin crear un hilo por línea. Turnos round-robin entre trabajos/líneas; máximo20 cuadros fuente,200 pares cuadro-línea y2 MiB de payload por captura. Presupuesto cooperativo5 ms de geometría por turno, comprobado entre cuadros, no watchdog duro; al vencer se confirma solo el prefijo realmente reducido. Leer alineados una vez, calcular fuera del lock, confirmar con CAS de generación/revisión/cursor y padre vigente. Liberar lock entre capturas/commits; descartar resultados obsoletos. No hay begin anidado ni cambio a journal SQLite necesario para esta feature.

Si una sola observación/cuadro excede el presupuesto seguro de payload, declarar solo sus líneas afectadas unavailable/count_work_limit, sin saltar un cuadro ni afirmar cobertura falsa. Preservar eventos existentes cuando una línea falla y no bloquear otras. El total se consulta por índice temporal y estado ready exige at_us<covered_until_us y at_us<available_until_us. No reconstruir dentro de GET.

### Frontend y reloj

Extraer cálculo puro de ancla `{wall_ms,source_us,rate}`. En marcha, target=source_us+(now-wall_ms)*1000*rate; al cambiar rate, muestrear usando el rate anterior y reanclar en ese mismo now. Pausa/espera conservan último cuadro pintado y ancla vacía. No reiniciar decoder ni caches por rate, ni aplicar nueva velocidad al tiempo transcurrido desde el ancla antigua. Seguir política de pausa al ocultar pestaña/inactivar workspace.

La barra vive dentro de progressive-viewer, antes de progressive-surface, para permanecer en fullscreen sin cubrir la escena. Controles/tarjetas reciben espacio propio; escena ocupa el alto restante. Una selección estable determina qué línea se arrastra; tarjetas permiten distinguir líneas coincidentes. Hooks validan contexto completo y el intervalo de validez exacta para el cuadro pintado. Cada cantidad lleva valid_until_us exclusivo, limitado por próximo evento, cobertura y prefijo; puede reutilizarse entre cuadros sin presentar números atrasados ni exigir una respuesta por RAF. Sin flecha, selector de sentido ni overlay numérico único en la experiencia nueva. El editor conserva pointer capture, traslación acotada y ajustes de teclado.

### Límites configurables nuevos

| Variable | Inicial | Validación |
| --- | ---: | --- |
| VIDEO_COUNT_MAX_LINES | 10 | entero10–32 |
| VIDEO_COUNT_MAX_ADMITTED_LINES | 128 | entero≥max_lines y≤1024; incluye tombstones |
| VIDEO_COUNT_REDUCER_BATCH_FRAMES | 20 | entero1–20 |
| VIDEO_COUNT_REDUCER_MAX_PAIRS | 200 | entero1–200 |
| VIDEO_COUNT_REDUCER_BUDGET_MS | 5 | positivo≤10; cooperativo |

Nombre2048 bytes,32 líneas de protocolo y payload2 MiB son techos de seguridad del contrato/worker, no opciones del request. El descriptor anuncia límites efectivos y32 colores iniciales únicos. No editar .env privado: documentar defaults sin secretos y pruebas con configuración aislada.

### Secuencia para generar tareas

1. Capturar referencia breve011 de publicación antes de editar producto; congelar contrato/modelo de estados y ejemplos.
2. Implementar DTO/validación, store/servicio, reducer/lifecycle, rutas/gateway e importación; verificar aislamiento de010.
3. Integrar borradores/editor/barra, normalización/color y recuperación con un poller agregado.
4. Integrar reloj/rate y sincronización sin cambiar decoder/fuente.
5. Ejecutar pruebas por riesgo, comparación breve0/1/10, imagen/video, accesibilidad/fullscreen y actualizar evidencias/auditoría. Separar validación humana y evaluación larga aún pendientes.

### Validation Strategy

Unitarias: geometría bidireccional seis clases, contacto/tangencia/extremos, identidad repetida/multilínea, normalización/grafemas/colores, reloj y estados de buffering. Integración: CAS simultáneo, idempotencia, eliminación/tombstone, recuperación/reinicio, importación y revisión obsoleta, cobertura exclusiva, rollback ante fallo, fairness/publicación y GET sin cambios de DB. Contratos/gateway: ejemplos positivos/negativos, query/body/permisos/origen/CSRF, cuatro operaciones nuevas y closed010 intacto.

Vitest: un poller, initial draft fiable tras fallo, selección por UUID, recuperación de mutación perdida, no pintura tardía/identidad eliminada y reloj. Playwright: fixture nueva con seis clases y movimientos opuestos, diez líneas, diez seek-cycles, veinte intentos fuera de prefijo,0,5×/1×/2× sobre30 s completos, cambios en pausa/buffer, controles360/768/1440, tacto/teclado/fullscreen. Imagen/inspección/exportación siguen sus regresiones. La prueba actual010 que exige Invertir sentido se adapta al nuevo flujo; conservar su prueba de API legacy por separado, sin declarar la UI vieja como vigente.

Comparador de rendimiento011 independiente: referencia de escritura única con hash/entorno, calentamiento y5 muestras; candidato0/1/10 líneas en régimen y catch-up, medir captura/lock/commit/GET/lag junto a publicación. Un resultado>5% frente a base se conserva y se investiga con pares AB/BA, sin sustituir referencia. La planificación no mide ni acredita estos objetivos. Guía reproducible en [quickstart.md](quickstart.md).

## Complexity Tracking

Sin violaciones constitucionales. Las tablas/contratos propios evitan romper consumidores cerrados y mezclar totales de distinto significado. CAS de colección sustituye endpoints CRUD por línea; el reducer reutiliza un worker, sin infraestructura distribuida ni inferencia duplicada.
