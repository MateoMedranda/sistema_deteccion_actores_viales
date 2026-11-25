# Implementation Plan: Inspección temporal de video, cruces dirigidos y resumen por clase

**Branch**: `feature/010-video-detalle-conteo` | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

**Input**: `specs/010-video-detalle-conteo/spec.md`, con confirmación expresa de un único sentido de conteo indicado mediante flecha.

**Estado de ejecución**: Implementación completada; consultar [audit.md](audit.md) y [validation.md](validation.md). El diseño histórico y la referencia previa se conservan; el coste sintético adicional fue investigado, sin declarar una mejora real de FPS.

## Summary

Unificar la ficha visual con imágenes y sustituir la selección basada solo en Track ID por contextos de inspección inmutables ligados al fotograma realmente pintado. Congelar el recorte de ese instante y enriquecerlo bajo demanda, sin escoger automáticamente el primer candidato de la trayectoria. El conteo nuevo exige cruce del segmento finito en el sentido elegido, con eventos únicos e históricos. Un inventario independiente consolida una clase por identidad confirmada para el resumen final. La exportación explícita incorpora etiquetas de clase/Track ID y una versión de renderer para no reutilizar MP4 antiguos sin etiquetas.

Este comando entrega diseño, contratos y guía de validación. No implementa funcionalidades, no crea tasks.md y no acredita pruebas de producto. Conserva el checkout principal, la rama actual, los cambios previos y las validaciones históricas pendientes.

## Technical Context

**Language/Version**: Python 3.12 para el entorno compatible existente; TypeScript 5.6/React 18 en frontend. No adoptar Python 3.15 para las dependencias actuales de OCR.

**Primary Dependencies**: FastAPI 0.115, Pydantic 2/pydantic-settings, SQLite estándar, PyAV 19.0.2, OpenCV, Pillow, YOLOv10/ByteTrack y los adaptadores de enriquecimiento ya cargados; Vite 5, React y mp4box 2.6.0. Sin cambio de motor, pesos, umbral, hilos ni cadencia. Para usar la fuente escalable incluida de Pillow, fijar su mínimo compatible en 10.1 y mantener el techo existente <12; el entorno actual ya admite esa API. No depender de fuentes de Windows ni descargarlas en ejecución.

**Storage**: Tablas aditivas en la base temporal configurada por VIDEO_JOB_DB_PATH y derivados privados bajo VIDEO_TEMP_DIR; padres p_video/p_frames existentes. Contextos, votos, eventos y variantes de exportación se retiran con el trabajo. Speckit/documentación permanecen en raíz.

**Testing**: pytest unitario/integración/contratos, JSON Schema/OpenAPI; Vitest/Testing Library; Playwright con servicios y medios sintéticos aislados. Comprobación visual de fichas y cuadros del MP4 descargado. Diagnósticos reales breves únicamente si hacen falta, sin repetir la comparación larga diferida.

**Target Platform**: Backend Windows/Linux según el entorno existente; navegador con reproducción progresiva. Validación visual a 360/768/1440 px, teclado y toque. Un proceso API mantiene la propiedad de workers/recursos actual; no añadir workers Uvicorn para acelerar este cambio.

**Project Type**: Aplicación web con frontend, API y gateway separados; servicios privados con sesiones/CSRF en gateway y API key/propiedad en API.

**Performance Goals**: Mantener el análisis sin decodificación adicional, OCR ni renderer nuevos cuando no se solicita inspección/exportación; inventario incremental O(observaciones nuevas), consultas de resumen O(identidades/clases consolidadas) y conteo por índice temporal. Publicar los agregados en la transacción del lote, sin escanear todo el video en cada GET. Comparar un tramo sintético controlado con la base y registrar medianas/entorno; investigar una regresión >5 % del análisis sin consultas/exportación. Este límite es criterio de implementación, no una medición ya realizada ni una promesa de 30 FPS.

**Constraints**: PTS fuente autoritativos, prefijo confirmado y cajas persistidas; no convertir tiempo a índice usando FPS nominal. Solo mediciones reales alimentan cruces y votos. Fuente privada con lease durante extracción, controles de propietario/generación/TTL antes de publicar, cola y bytes acotados. Extraer/enriquecer fuera del lock de SQLite; la extracción usa un subproceso efímero PyAV sin modelos, con watchdog terminate/join que incluye arranque en el plazo de5s; usar el slot compartido existente para llamadas a modelos. La consulta no vuelve a ejecutar el detector de escena ni amplía TTL.

**Scale/Scope**: Cinco historias, FR-001–FR-024, SC-001–SC-009. Límites iniciales propuestos para inspección: un worker, 20 contextos en cola global, 128 contextos retenidos y 128 MiB derivados por trabajo, 8 MiB por recurso, extracción hasta 300 cuadros decodificados o 5 s de pared, vencimiento mínimo entre padre y TTL de enriquecimiento. Se harán configurables con validación positiva; no son cifras de rendimiento demostradas. Reducers de conteo/backfill procesan como máximo 200 cuadros por transacción y ceden el lock entre lotes. Una insuficiencia se declara, no se elude creando evidencia de otro instante.

## Constitution Check

*GATE: evaluación previa a Phase 0 y posterior a Phase 1; sin excepciones solicitadas.*

| Principio | Antes de investigación | Después del diseño |
|---|---|---|
| I. Modularidad/contratos | PASS: frontend/API/gateway existentes | PASS: servicios/adaptadores específicos y contratos aditivos; rutas no cargan modelos |
| II. Validación/trazabilidad | PASS: requisitos y casos de error definidos | PASS: cuerpos/queries cerrados, generación, revisiones y logs seguros de fases/latencia |
| III. Privacidad | PASS: autorización/TTL vigentes | PASS: medios derivados privados, límites, leases y limpieza de todas las tablas/archivos nuevos |
| IV. Pruebas/calidad | PASS: no cambia detector/pesos/preprocesado | PASS de diseño: matriz unitario/integración/imagen/video/visual; ejecución pendiente de implement |
| V. Recursos/rendimiento | PASS: sin benchmark largo ni trabajo nuevo automático | PASS: workers acotados, agregados incrementales, GET sin efectos y perfiles separados |

Ninguna gate exige cambiar la constitución. No se afirma que las pruebas previstas hayan pasado. Pendientes largos/humanos de 009 no se cierran con esta planificación.

## Project Structure

### Documentation (this feature)

```text
specs/010-video-detalle-conteo/
├── spec.md
├── checklists/requirements.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── README.md
    ├── ui.md
    ├── openapi-additions.yaml
    ├── schemas.json
    └── examples.json
```

tasks.md se generará exclusivamente en la siguiente fase.

### Source Code (repository root)

```text
backend/app/
├── api/routes/video_playback.py               # conservar rutas previas; conectar contratos nuevos
├── api/routes/video_inspections.py           # nuevo, contexto y medios privados
├── api/routes/video_directed_count.py        # nuevo, configuración/lecturas
├── api/routes/video_detection_summary.py     # nuevo, capacidades/resumen
├── domain/                                  # modelos nuevos + class_presentation existente
├── adapters/timed_video_decoder.py           # compartir conversión aprobada, sin cambiarla
├── adapters/selected_frame_extractor.py      # nuevo, seek/PTS exacto y límites
├── services/video_inspections.py             # nuevo, contexto/cola/leases/resultados
├── services/directed_counting.py             # nuevo, geometría y reducer
├── services/detection_inventory.py           # nuevo, votos e inventario
├── services/video_export_labels.py          # nuevo, layout de cuadro y texto
├── services/video_progressive_store.py       # commit de agregados/limpieza
├── services/progressive_export.py            # orquestación única, variante versionada
├── core/config.py, lifespan.py, logging.py
└── web/proxy.py                              # allowlist exacta, sin credenciales en cliente
backend/tests/{unit,integration,contract}/
frontend/src/
├── features/image-analysis/VehicleDetails.tsx
├── features/image-analysis/{EvidenceCrop,PlateComparison}.tsx
├── features/video-analysis/{VideoWorkspace,ProgressiveVideoPlayer,ProgressiveTrackResults,ProgressiveCountTools,VideoExport}.tsx
├── services/apiClient.ts                     # helper de descarga con renderer/job/ruta validados
├── features/video-analysis/{useVideoInspection,useDirectedCount,useDetectionSummary}.ts  # nuevos
├── features/video-analysis/{DetectionSummary,VideoInspectionDetails}.tsx                 # nuevos
├── components/vehicle-details/              # presentación compartida; adaptadores separados
└── styles.css
frontend/tests/features/{image-analysis,video-analysis}/
frontend/e2e/                               # escenarios 010, sin medios privados
```

**Structure Decision**: Extender el monorepo existente; no mover backend/frontend ni Speckit. Los nombres nuevos son destinos previstos, no archivos implementados. Mantener endpoints/servicios legacy y reutilizar orquestación, procesador de atributos/placas, colores y editor actuales sin copiar lógica de modelo.

## Phase 0 — Research

Completada mediante inspección de código en tres investigaciones de solo lectura: contexto/evidencia, geometría/inventario y UI/exportación. [research.md](research.md) registra causas verificadas, decisiones, alternativas y fuentes primarias. No quedan incógnitas bloqueantes; las capacidades antiguas insuficientes tienen estados explícitos.

## Phase 1 — Design

### Paquetes de backend previstos

| Paquete | Diseño | Cobertura |
|---|---|---|
| B1 | Contextos inmutables por generación/track/cuadro; extracción exacta y cola reutilizable, recursos/TTL | FR-004–FR-008, FR-023 |
| B2 | Conteo dirigido del segmento, configuración con revisión y reducer histórico de mediciones | FR-009–FR-015 |
| B3 | Inventario de identidades/votos de clase independiente de enriquecimiento/conteo | FR-016–FR-018 |
| B4 | Renderer completo con etiquetas/Unicode y caché de exportación versionada, sin inferencia | FR-019–FR-021 |
| B5 | Contratos/gateway, migración aditiva, capacidades, límites, recuperación y limpieza | FR-022–FR-024, transversal |

### Diseño de interacción

- Ficha: presentación común con imágenes y datos adaptados por origen; retirar max-height/overflow de toda `.progressive-details`. Conservar ampliación interna de placa cuando corresponde, scroll de página y cierre/foco accesibles.
- Selección: pausar y capturar job/generation/Track ID/índice del cuadro realmente pintado. Nuevo contexto al seleccionar otro instante. El polling completa datos sin sustituir asset_id ni resetear zoom. Buscar/reanudar cierra la inspección vigente; respuestas retrasadas no la reabren. Reabrir exactamente el mismo contexto reutiliza sus recursos/resultados válidos.
- Editor: decodificar el primer fotograma local del archivo seleccionado antes del envío, con URL temporal revocada al cambiar archivo. Mantener borrador por generación de archivo; después de aceptar el trabajo aplicar línea/sentido mediante el contrato nuevo, sin reenvío de video. Si la carga se recupera, vincular solo al job de esa intención.
- Conteo: flecha transversal calculada en píxeles fuente, botón invertir, aplicar/cancelar borrador; indicador superior derecho con un solo total. Durante actualización conservar dato confirmado etiquetado con su tiempo; tras seek/revisión distinta no presentarlo como actual. El nuevo resultado solo se publica si coinciden selección de consulta, generación y revisión.
- Resumen: sección independiente «Vehículos detectados en todo el video», bajo reproductor/exportación y antes del editor. No reemplaza «vehículos de este fotograma» ni el contador de cruces. Parcial/definitivo/cobertura visibles.

### Secuencia y compatibilidad

1. Contratos, estados y migración aditiva; fixtures que fallen por carencia de capacidades nuevas.
2. B1 y ficha temporal; B2 y B3 pueden desarrollarse por separado sobre observaciones persistidas.
3. Editor previo al análisis/indicador y resumen; B4 con variante explícita y evidencia visual.
4. Integración B5, pruebas cruzadas, retirada/reinicio, comparación acotada y documentación de resultados.

No se reinterpretan `/summary`, `/playback/count` ni `/tracks/{id}/enrich`. La UI 010 usa rutas nuevas y un selector de renderer opt-in. La UI antigua conserva sus respuestas. Un recurso antiguo sin fuente/procedencia suficiente informa unavailable/reanalysis_required; no se inventa un resultado final. La migración no elimina tablas ni archivos previos.

### Refinamientos del análisis A1/U1

La elegibilidad de cruce se evalúa únicamente con la clase medida en la observación que confirma el paso, normalizada con strip/lower. Se admiten car, truck, bus, van, pickup, suv, sedan, hatchback, mpv, estate, bicycle y motorcycle; person, vacío y clases no catalogadas no suman cruces. Todas las mediciones conservan el estado geométrico de la trayectoria; un paso excluido por clase no consume la elegibilidad para un futuro cruce válido. Guardar class_key_at_crossing inmutable en el evento y no reevaluarlo con votos futuros, clasificación consolidada u OCR. Esta política no restringe el resumen: sus clases no catalogadas siguen visibles con requires_review.

Antes de modificar backend/app o frontend/src en la iteración, T001 creará un comparador autocontenido en backend/tests/performance/test_video_detail_overhead.py, basado en los fixtures/runners de rendimiento existentes. Su fuente sintética y detector controlado no dependerán de T002 ni de APIs nuevas. Una ejecución de calentamiento y al menos tres medidas capturan mediana de tiempo de análisis/publicación, tamaño de lote/observaciones, entorno/paquetes, hash del fixture y huella del código fuente de base en evidence/publication-baseline.json. No persistir medios o credenciales. La línea base identifica el código anterior a010, aunque ya existan commits documentales de010.

La referencia se escribe una sola vez con modo explícito de captura; no se sobrescribe en comparación ni se recaptura después de empezar a cambiar producto. T071 usa el mismo harness/fixture/parámetros, calentamiento y al menos tres medidas del candidato, compara medianas/etapas y conserva ambas huellas en publication-overhead.json. Si falta referencia o cambia el fixture/entorno necesario para comparar, se declara validación pendiente/fallida; no se genera una referencia del candidato ni se afirma mejora. Investigar >5 % de regresión sin consultas/exportación. Solo es comparación sintética breve y no valida FPS reales ni sustituye la evaluación larga diferida.

### Validación y trazabilidad

| Historias / requisitos | Prueba futura y evidencia | Criterios |
|---|---|---|
| US1 / FR-001–003 | Capturas 360/768/1440, ficha imagen/video, scroll/foco/teclado/toque | SC-001,009 |
| US2 / FR-004–008 | Misma identidad en 3 s/20 s; POST perdido; respuestas invertidas; 30 s sin cambios de asset ni zoom | SC-002,003 |
| US3 / FR-009–015 | Geometría pura y cronología; extremos/contactos/prolongación/sentido inverso; editor antes de POST; dos recorridos/cinco saltos | SC-004,005,009 |
| US4 / FR-016–018 | Votos/ties/desconocidos/personas; 100 cuadros una identidad; cero/parcial/final, reinicio y batch repetido | SC-006 |
| US5 / FR-019–021 | Layout y glifos; MP4 decodificado; versión antigua vs nueva; detector parcheado para prohibir inferencia | SC-007,008 |
| FR-022–024 | Contratos antiguos, gateway/CSRF, propietario ajeno, expiración en trabajo, limpieza y registro de commits | SC-008 y regresiones |

Ejecutar una imagen y un video sintéticos end-to-end, suites backend/frontend y build; ampliar a pruebas reales breves solo si resuelven un riesgo abierto. No iniciar comparaciones largas ni pruebas humanas previamente diferidas. Registrar qué se ejecutó, entorno y resultados, sin confundir revisión documental de esta fase con aceptación del producto. Guía: [quickstart.md](quickstart.md).

## Complexity Tracking

Sin violaciones de constitución. Las rutas/tablas nuevas evitan reinterpretar clientes y resultados históricos; no introducen un segundo backend, segundo detector ni nueva infraestructura. La complejidad de colas/PTS/leases es necesaria para evitar bloqueo, evidencia equivocada y retención indebida.
