# Implementation Plan: Video progresivo con navegación acotada

**Branch**: `feature/009-video-progresivo` | **Date**: 2026-11-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/009-video-progresivo/spec.md`

## Summary

Publicar un prefijo continuo de cuadros y anotaciones durante la inferencia, reproducir el MP4 original protegido y admitir sus píxeles/cajas juntos en canvas solo dentro del intervalo confirmado. Controles propios permiten retroceder y volver al límite sin repetir inferencia. Enriquecer evidencia por Track ID durante el mismo recorrido, publicar resultados provisionales y finalizar con la política top-K actual. Fallos técnicos conservan resultados confirmados hasta su plazo; cancelación explícita y vencimiento los retiran.

El resultado progresivo tiene estados independientes del trabajo/exportación legacy. La API de imágenes, detecciones finales, MP4 anotado y conteo mantienen sus contratos. Documentación de diseño; no se ha implementado ni medido esta solución.

## Technical Context

**Language/Version**: Python 3.12, TypeScript 5.6, React 18; se conserva backend/.python-version y el entorno compatible existente.

**Primary Dependencies**: FastAPI 0.115, Pydantic Settings, SQLite, OpenCV, FFmpeg/ffprobe, Ultralytics/Torch y adaptadores aprobados de atributos/placa. Incorporar durante implementación únicamente PyAV av==19.0.2 y su resolución en uv.lock para PTS durante el decode. Frontend usa Vite, canvas, WebCodecs/VideoFrame y mp4box2.6.0 para demux MP4; no añade servicio de streaming. Véase la enmienda de implementación.

**Storage**: Tablas aditivas en backend/.runtime/video-jobs.sqlite3 para prefijo, cuadros, observaciones, unidades y revisiones. Fuente aceptada y recortes privados con recibos de propiedad/vencimiento; directorio backend/.runtime/video-progressive/. Archivos cerrados antes de publicar referencias. No historial permanente.

**Testing**: pytest/pytest-cov/jsonschema, pruebas contractuales e integración, Vitest/Testing Library y Playwright; corpus sintético de tiempos conocidos y validación separada con modelos reales. Prueba de uso de cinco personas.

**Target Platform**: Checkout principal Windows x64/Python 3.12 como referencia; servidor/gateway en loopback y navegadores de escritorio, tablet y móvil. Referencia de navegador fijada por el lock de Playwright; validación real adicional Chromium, Firefox y WebKit actuales que soporten el flujo de callbacks/canvas.

**Project Type**: Aplicación web con microservicio de inferencia y gateway privado existente; backend/ y frontend/ separados.

**Performance Goals**: Inicio <=2 s tras cinco segundos confirmados; 95 % de 30 saltos <1 s; datos enriquecidos <=2 s tras publicarse; desfase <=un intervalo de cuadro; 95 % de ventanas de reproducción a >=90 % del FPS de origen a 1x; coste temporal <=110 % y RSS conjunta <=120 % del baseline. Esperas de análisis se informan aparte, no se eliminan de los resultados.

**Constraints**: Sin alterar modelo, pesos, umbrales, muestreo, significado processed-cfr ni límites privados de admisión. El original no es una fuente visible ni audible durante reproducción progresiva. Acceso por propietario/sesión y TTL existentes; el bloqueo es del reproductor y no confidencialidad de bytes frente al propietario. No prometer tiempo real si la CPU procesa más lento que el video.

**Scale/Scope**: Una reproducción activa por usuario/trabajo; concurrencia de trabajos configurada existente. Lotes <=15 cuadros o 0,5 s; página <=1 MiB/1.000 observaciones/100 fragmentos de cuadro, sin truncado; consulta temporal <=30 s. Poll visible cada500ms, una petición de estado en vuelo. Caché cliente <=16 MiB y30 s acumulados de anotaciones, como máximo cuatro páginas en vuelo; cola RAM <=32 referencias y una evaluación de evidencia activa. K existente de evidencia por track, máximo K+1 evaluaciones únicas.

## Constitution Check

*GATE: evaluación previa a Phase 0 y repetida después del diseño Phase 1.*

| Principio | Antes de investigación | Después del diseño |
|---|---|---|
| I Modularidad y contratos | PASS: mantener API/servicios/adaptadores separados | PASS de diseño: decoder, store, servicio de reproducción y scheduler propios; contratos aditivos |
| II Validación y trazabilidad | PASS: conservar admisión y errores seguros | PASS de diseño: validar tiempo/cursor/Range, métricas por lote/fase, sin medios o lecturas en logs |
| III Seguridad y minimización | PASS: mismo propietario, secreto servidor, TTL | PASS de diseño: acceso a original/evidencia acotado, retirada atómica y cleanup; solo conservar medios necesarios del resultado vigente |
| IV Calidad verificable | PASS: ninguna sustitución de modelo autorizada | PASS de diseño: comparación del decoder, top-K final equivalente, regresiones y gates humanos/reales expresos |
| V Rendimiento | PASS: corpus/baseline antes de medir | PASS de diseño: decode único, modelos únicos, colas/cachés acotadas y gates110/120 % |

No se solicita excepción constitucional. PASS de diseño no equivale a superar gates de implementación: si falla equivalencia, seguridad, frontera visible o coste, no se declara la iteración aceptada ni se relajan criterios.

## Project Structure

### Documentation (this feature)

~~~text
specs/009-video-progresivo/
├── spec.md
├── checklists/requirements.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── validation-plan.md
├── contracts/
│   ├── README.md
│   ├── openapi-additions.yaml
│   ├── schemas.json
│   ├── examples.json
│   ├── gateway.md
│   └── player.md
└── tasks.md                 # fase posterior; no generado aquí
~~~

### Source Code (repository root)

~~~text
backend/
├── app/
│   ├── adapters/timed_video_decoder.py              # nuevo
│   ├── api/routes/video_playback.py                 # nuevo
│   ├── domain/{models,schemas}.py
│   ├── services/
│   │   ├── {video_processing,video_job_store,video_worker,video_artifacts}.py
│   │   ├── {enrichment_job_service,enrichment_worker,enrichment_processing}.py
│   │   ├── video_progressive_{store,service}.py       # nuevos
│   │   ├── progressive_evidence.py                  # nuevo
│   │   ├── progressive_enrichment.py                # nuevo
│   │   └── temporary_cleanup.py
│   ├── core/{config,lifespan}.py
│   └── web/{proxy,main}.py
├── tests/{unit,integration,contract,performance,e2e}/
├── scripts/evaluate_video_progressive.py            # nuevo arnés
├── pyproject.toml
└── uv.lock
frontend/
├── src/features/video-analysis/
│   ├── VideoWorkspace.tsx
│   ├── {useVideoAnalysis,videoAnalysisReducer,videoTypes}.ts
│   ├── ProgressiveVideoPlayer.tsx                   # nuevo
│   ├── {useProgressivePlayback,playbackReducer,progressiveTypes}.ts
│   ├── VideoTimeline.tsx                           # nuevo
│   └── ProgressiveTrackResults.tsx                 # nuevo
├── src/services/apiClient.ts
├── tests/features/video-analysis/
└── e2e/video-progressive*.spec.ts
.specify/ .agents/ specs/ metricas/                  # permanecen en raíz
~~~

**Structure Decision**: Extender los módulos actuales e incorporar responsabilidades nuevas sin trasladar otra vez el proyecto, crear nuevos procesos de modelos ni mezclar datos de pruebas con .runtime del usuario. Los nombres nuevos son la asignación prevista para tasks; no existen por este plan.

## Phase 0 — Research

Completada en [research.md](research.md). Decisiones: cronología PTS con PyAV, prefijo transaccional con cuadros vacíos, salida visible admitida por canvas, Range privado, polling acotado, enriquecimiento provisional top-K y conservación parcial. Las alternativas y fuentes primarias están registradas. No hay aclaraciones técnicas abiertas.

## Phase 1 — Design & Contracts

Los estados y reglas están en [data-model.md](data-model.md); la API aditiva y sus ejemplos, en [contracts/README.md](contracts/README.md); las fronteras de sesión/Range, en [contracts/gateway.md](contracts/gateway.md), y el comportamiento visible, en [contracts/player.md](contracts/player.md).

Orden de dependencias para la siguiente fase:

| Paquete | Cambio y resultado revisable | Dependencias | Requisitos |
|---|---|---|---|
| B1 | decoder con PTS, equivalencia, migración SQLite aditiva y batch transaccional incluyendo vacíos/cajas display | baseline congelado | FR001–003,009–010,022 |
| B2 | recurso progresivo, fuente Range, snapshots/páginas, retiro/TTL, recuperación tras fallo y compatibilidad de exportación/conteo | B1 | FR004–008,011,017–020,023 |
| B3 | evidencia inmaculada durante el decode, top-K online, cola durable y unidades/revisiones progresivas | B1,B2 | FR012–015,018,020 |
| B4 | reutilización de modelos/consenso, evidencia autorizada y adaptador de enriquecimiento final legacy sin re-inferencia | B3 | FR011–015,022–023 |
| G1 | allowlist y preflight propios, validación temporal/cursor, Range/HEAD específico, revocación en stream | B2,B4 | FR019–020 |
| F1 | cliente/parser nuevos, caché acotada, estado de intención/prefijo, montaje mientras analiza | B2,G1 | FR001–008,016–019 |
| F2 | canvas con admisión, timeline y fullscreen propios, selección/lista accesible por Track ID y datos incrementales | F1,B4 | FR009–015,021 |
| V1 | contratos, concurrencia, regresión imagen/video/conteo, benchmarkAB/BA y prueba humana | todos | SC001–010 |

Este orden define paquetes, no reemplaza tasks.md. Se deben generar tareas pequeñas y trazables sin implementar durante plan.

### Compatibilidad y activación

- POST /api/v1/video-jobs sin query mantiene modo legacy. El nuevo cliente pide presentation=progressive; su respuesta de aceptación conserva el esquema previo.
- API nueva bajo /api/v1/video-jobs/{job_id}/playback; no convertir /detections o /summary existentes en listas parciales.
- completed y processed-cfr mantienen significado para MP4 final/conteo. Cronología source-pts y análisis progresivo se guardan aparte.
- Fallo de exportación deja legacy failed y progresivo complete cuando todos sus cuadros se confirmaron. Un timeout de análisis deja partial_failed y no pierde el prefijo.
- DELETE del recurso playback revoca progresivo y los recursos derivados de ese trabajo, incluso después de completado/fallado; no altera rutas ni reglas de trabajos legacy sin recurso progresivo.
- La ruta POST de enriquecimiento actual sigue teniendo fuente completed y unidades finales. En trabajos progresivos terminados reutiliza un adaptador final de los resultados top-K cacheados, sin otra decodificación/evaluación; clientes existentes no ven denominadores provisionales.
- No se cambia automáticamente VIDEO_JOB_TIMEOUT_SECONDS ni MAX_VIDEO_DURATION_SECONDS; el arnés configura valores propios idénticos para ambos brazos. El despliegue habilita el modo progresivo solo tras gates; los clientes legacy continúan funcionando.

## Validation & Release Gates

[validation-plan.md](validation-plan.md) fija corpus, metodología, umbrales y matriz SC. [quickstart.md](quickstart.md) distingue comandos actuales de los escenarios que deben existir al implementar.

Gates: documentación coherente → equivalencia decoder/cronología → publicación/seguridad/cancelación → salida visible/frontera/FPS → integración y regresiones → coste de modelos reales → prueba de cinco usuarios. Un fallo conserva evidencia y nuevas tareas; no se anuncia aceptación integral con mocks o capturas.

## Complexity Tracking

No hay violaciones que justificar. PyAV es la única dependencia nueva prevista y resuelve PTS en el mismo decode; canvas evita una segunda cadena de fragmentación/transcodificación. No se incorpora un servicio de colas, streaming externo o almacén permanente.

## Verificación documental de esta etapa

- Phase 0 y Phase 1 completas; constitución reevaluada sin excepciones de diseño.
- JSON Schema validado: 16 tipos; seis ejemplos válidos y tres ejemplos negativos rechazados.
- OpenAPI aditivo: siete rutas, nueve operaciones, referencias y parámetros resueltos; enlaces locales verificados.
- Prerrequisitos Speckit resuelven la iteración 009 en el checkout principal.
- Hooks after_plan revisados: no hay registrados.
- No se ejecutaron modelos, benchmarks ni pruebas del producto porque esta etapa genera diseño; sus resultados permanecen pendientes para implementación. No se creó tasks.md.

## Integración explícita y nombres públicos

La composición de `backend/app/main.py` y `backend/app/core/lifespan.py` debe crear/injectar una sola instancia de store y servicio progresivos, registrar sus rutas y reutilizar los modelos existentes. El worker se incorpora al mismo ciclo de vida al implementar US3; se inicia una sola vez y se detiene antes de cerrar sus stores. No crear otra app global ni otro conjunto de modelos. Las pruebas de arranque/cierre con fakes verifican estas relaciones y la liberación de recursos; las reglas de conservación y retirada de resultados siguen el modelo de datos.

Los nombres públicos canónicos son `PlaybackState.revision`, `PlaybackState.enrichment.status` y `PlaybackState.enrichment.revision`. El parámetro snapshot de tracks contiene el valor de enrichment.revision; no se añaden alias planos. Los modelos persistentes pueden usar nombres internos, pero el serializador y los ejemplos siguen exactamente schemas.json.


## Enmienda de implementación — 2026-11-22

Las pruebas de píxeles bajo carga descartaron la copia de HTMLVideoElement mediante requestVideoFrameCallback. La salida final usa VideoFrame inmutable de WebCodecs, con identidad de muestra y PTS contrastados con cada cuadro publicado. mp4box2.6.0 lee metadatos por rangos; @types/node22 se usa solo al probar fixtures. No cambia el contrato API ni se expone video original como fallback. El contrato actualizado está en contracts/player.md.

La cronología de PyAV conserva el perfil de conversión BGR de OpenCV (ITU601/BICUBIC) mediante reformatter persistente. Se verificaron los3.611 cuadros reales sin diferencias de píxeles. Publicación de sightings por lote, ranking top-K ligero y refresco de resultados solo ante cambios evitan trabajo SQLite repetido; no cambian modelo, umbrales, tracking ni selección final.

Pruebas consolidadas usan test_progressive_api/store/lifecycle/race/security/workers, test_progressive_topk/color, playbackReducer/progressive/recovery/trackResults y los dos archivos E2E video-progressive-navigation/recovery. Sus nombres sustituyen archivos separados previstos, conservando la trazabilidad de tareas.

El usuario solicitó cerrar la entrega funcional y diferir la comparación larga. No se rebajan SC007/010 ni se toma un resultado parcial o de otro candidato como aceptación. También quedan pendientes la prueba humana y las verificaciones exhaustivas indicadas en validation.md.


## Enmienda aprobada: inspección bajo demanda y conteo opcional

El nuevo frontend envía `presentation=progressive&enrichment=on-demand`. Sin enrichment se conserva el modo automático existente. La migración aditiva guarda p_video.on_demand y solicitudes/evidencias fijadas por Track ID; la cola solo reclama evidencias solicitadas en ese modo. Cada solicitud toma hasta K evidencias confirmadas y termina aunque la fuente continúe abierta. Repeticiones reutilizan la solicitud y sus resultados; no hay OCR por GET, seek o conteo. Los recortes siguen siendo PNG originales y mantienen autorización/TTL. `final` en este modo identifica final de la consulta congelada, no del análisis completo.

POST playback/tracks/{track_id}/enrich solicita consulta idempotente. PUT/GET/DELETE playback/count configura, consulta al instante at_us o desactiva conteo. ProgressiveCountService usa p_frames/raw_bbox y los criterios existentes de lado/dirección, sin decoder/modelos, persiste último lado y un evento por track y permite backfill al dibujar tarde. Los eventos llevan source-PTS. Cambio de línea incrementa revisión y recalcula; navegación solo consulta acumulados históricos. Son derivados privados del mismo recurso; retirada y TTL los invalidan y limpian.

Frontend: la ficha lateral comparte estilos de Imagen; una lista compacta del fotograma queda plegada debajo de controles. ProgressiveCountTools captura un canvas confirmado y admite dos puntos por toque/puntero o rangos de teclado. useProgressiveCount consulta acumulados y descarta respuestas fuera de contexto; el canvas principal dibuja la línea y su esquina superior derecha muestra el contador. No se monta el editor legacy duplicado para clientes managed. Imágenes y conteo final legacy permanecen.

Esta modificación reduce trabajo automático, no constituye una medición de nuevos FPS. Los gates reales previos siguen abiertos y requieren distinguir políticas al comparar; no se presenta una corrida con enriquecimiento deshabilitado como equivalencia del protocolo automático original.


### Corrección del seguimiento y restauración de edición

El adaptador registraba model.track con persist=False en el primer cuadro. La versión instalada captura ese valor en callbacks; on_predict_start vuelve a crear el tracker en cada predicción. Se sustituye esa integración por predicción raw con los mismos pesos/umbral/dispositivo y BYTETracker independiente por trabajo usando bytetrack.yaml existente. No se añaden callbacks de seguimiento al modelo compartido, por lo que imágenes intercaladas no avanzan su tracker. Reset inicia una nueva sesión sin recargar el detector.

La primera muestra confirmada se copia desde VideoFrame a un canvas de preview acotado a1280px de ancho, con la misma orientación. No hay otro decode. El editor lo muestra automáticamente, con captura de puntero y arrastre de extremos o segmento completo, traslación acotada, teclado y ajustes secundarios plegados. Se mantiene el conteo progresivo previamente implementado.

La corrección modifica identidades previamente incorrectas; no se fuerza equivalencia con las asociaciones defectuosas de la referencia. El ensayo corto de40cuadros y las regresiones de orden/imagen intercalada son evidencia de esta corrección, no aceptación de toda la precisión ni del benchmark pendiente.
