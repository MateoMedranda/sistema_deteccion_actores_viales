# Implementation Plan: Anotaciones despejadas y placas legibles

**Branch**: `feature/007-anotaciones-placas-legibles` | **Date**: 2026-11-20 | **Spec**: [spec.md](spec.md)
**Input**: Iteración 007; planificación en checkout principal, conservando el trabajo existente. La rama solicitada ya se creó sin alterar contenido de archivos ni índice.

## Summary

Usar el original canónico como escena y dibujar una sola capa de contornos con colores por clase. Trasladar toda identificación a una banda externa con prioridad foco > puntero > selección; la ficha solo cambia al activar un vehículo. La lista resuelve cajas pequeñas/solapadas. Se conservan las rutas antiguas de anotación y los flujos de video/conteo.

Añadir una versión visual de placa generada bajo demanda desde la misma evidencia autorizada, mediante perfil determinista sin reconstrucción generativa. Un GET protegido devuelve PNG y metadata tipada, sin volver a ejecutar detección/localización/OCR. Mantener el original y separar procedencia visual de procedencia de lectura.

Congelar la lectura actual como baseline-v1. Preparar una candidata de rescate y un evaluador reproducible con datos privados reservados; la política normal sigue siendo baseline-v1 hasta demostrar SC-006. La mayor exactitud es un criterio pendiente de medición, nunca una promesa derivada de una imagen más nítida.

## Technical Context

**Language/Version**: Python 3.12 y TypeScript 5.6.3.
**Primary Dependencies**: Versiones locales inspeccionadas: FastAPI 0.115.14, Pydantic 2.14.1, Pillow 11.3.0, OpenCV headless 4.14.0.94, NumPy 2.3.5, psutil 7.2.2; React 18.3.1, Vite 5.4.21, Vitest 2.1.9 y Playwright 1.65.1. Se mantienen manifests/lockfile; no instalar ni actualizar dependencias de producción por este plan.
**Storage**: Estado/Blob de sesión; originales/SQLite temporales existentes; nueva caché RAM de derivados con TTL absoluto y tamaño acotado. Sin nueva tabla, servicio externo ni archivos persistentes de placas.
**Testing**: pytest/httpx, Vitest/Testing Library, Playwright; pruebas de geometría, CORS, privacidad, concurrencia, caducidad, uso de recursos, estado visual y evaluación real separada.
**Target Platform**: Backend local Windows/Python y navegadores modernos; Chromium en 360/768/1440 CSS px, teclado/toque y texto 200%.
**Project Type**: Aplicación web React con servicio FastAPI modular existente.
**Performance Goals**: Contexto/ficha <1 s con datos cargados. Derivada visual p95 <=2 s sobre >=30 placas válidas; todo intento local termina <=10 s. Janitor <=2 s. Medir coste OCR adicional por separado, sin adjudicar RSS exclusivo a una operación concurrente.
**Constraints**: Colores sólidos; contraste 4.5:1 texto/3:1 controles-foco; alternativa táctil 44 px. Sin texto/glifos sobre la escena, sin secretos en URLs/logs, sin cambios a modelos/pesos/umbrales, sin reconstruir caracteres.
**Scale/Scope**: Una fuente y selección activas. Una derivada CPU activa por proceso, sin cola; caché 8 entradas/16 MiB, PNG <=2 MiB, lado <=2048 y <=2 Mpx. Son límites nuevos de la derivada, no cambios a los límites existentes de imágenes.

## Constitution Check

| Principio | Antes de investigación | Después del diseño |
|---|---|---|
| I Modularidad/contratos | PASS: ampliar capas existentes. | PASS: perfiles puros, servicio/store de preview, API fina y DTO explícitos; sin segundo motor de inferencia. |
| II Validación/trazabilidad | PASS: conservar identidad/geometría. | PASS: ROI derivado del resultado servidor, metadata validada, errores seguros y mediciones correlacionadas. |
| III Seguridad/datos | PASS: mismo dueño y TTL. | PASS: acceso antes/después de proceso y en hits; no-store; RAM acotada, purga, sin envío a terceros ni textos de candidatas descartadas. |
| IV Pruebas/modelo | PASS: ninguna promoción por confianza. | PASS: línea base congelada, evaluación reservada, modelos/umbrales iguales y promoción condicionada a SC-006; regresión de imagen/video. |
| V Recursos/rendimiento | PASS: sin inferencias repetidas por UI. | PASS: threadpool/cupo acotados, single-flight, presupuesto temporal y recursos retenidos hasta terminar el hilo real; medición pendiente, no afirmada. |

Sin excepción constitucional. El plan puede implementarse sin pesos/medios nuevos, usando fixtures para lógica; acreditar mayor exactitud requiere las referencias y condiciones de evaluación. T067/T068 de 006 mantienen su estado independiente.

## Project Structure

### Documentation (this feature)

```text
specs/007-anotaciones-placas-legibles/
  spec.md
  checklists/requirements.md
  plan.md
  research.md
  data-model.md
  evaluation-protocol.md
  contracts/frontend-interactions.md
  contracts/backend-additions.md
  contracts/openapi-additions.yaml
  quickstart.md
  tasks.md                         # salida posterior de speckit-tasks
```

### Source Code (repository root)

```text
frontend/src/features/image-analysis/
  AnnotatedImageViewer.tsx          # escena limpia, conservar nombre por compatibilidad interna
  ImageWorkspace.tsx
  DetectionList.tsx
  VehicleDetails.tsx
  useImageAnalysis.ts               # original como fuente principal; no descargar anotada para visor
  imageAnalysisReducer.ts
  image-analysis.css
  classPresentation.ts             # nuevo registro compartido
  DetectionContext.tsx             # nuevo contexto externo
  ClassLegend.tsx                  # nuevo
  PlateComparison.tsx              # nuevo original/procesada y zoom local
  usePlatePreview.ts               # nuevo lifecycle acotado por selección/generación
frontend/src/services/apiClient.ts  # PNG + cabecera tipada + deadline completo
frontend/src/services/apiTypes.ts
frontend/src/utils/imageGeometry.ts
app/api/routes/enrichment_jobs.py   # GET derivada protegida
app/domain/schemas.py              # metadata y provenance aditivas
app/main.py                        # exponer una cabecera CORS adicional
app/core/lifespan.py                # servicio/caché y janitor/cierre
app/services/
  plate_preview_service.py          # nuevo, orquesta acceso/ROI/proceso
  plate_preview_store.py            # nuevo, RAM/single-flight/límites
  plate_geometry.py                 # nuevo helper relativo->ROI entero común al preview
  plate_profiles.py                # nuevo, recetas versionadas puras
  plate_reading_policy.py           # nuevo baseline/candidata inyectables
  plate_quality.py                  # baseline existente preservada
  enrichment_processing.py          # provenance e inyección de política solo imagen
  enrichment_results.py             # normalización/saneamiento de metadata nueva
  enrichment_job_store.py           # acceso por identidad a resultado, no posición/página
  inference_metrics.py             # reutilizar contexto, conservar semántica T083
scripts/evaluate_plate_profiles.py  # futuro evaluador agregado sin evidencia sensible
tests/{unit,integration,contract,e2e,performance}/
frontend/tests/features/image-analysis/
frontend/e2e/
```

**Structure Decision**: Reutilizar cliente HTTP, geometría, autorización y limpieza existentes. Los archivos nuevos anteriores son destinos de implementación futura; este comando no los crea. No modificar anotación de video ni endpoint annotated-image para resolver la escena de 007.

## Phase 0 — Research decisions

[research.md](research.md) cierra decisiones de escena, contexto, paleta, perfiles, almacenamiento, procedencia y evaluación. Dos agentes investigaron en modo solo lectura. No quedan aclaraciones técnicas abiertas. La falta de un conjunto privado de referencia es dependencia de aceptación, no una decisión de arquitectura pendiente.

## Phase 1 — Design

### Escena y controles

1. Reusar original_image autenticado y ya validado de 006. No hacer fallback a annotated-image ni al archivo de carga orientado de forma distinta. Si el original falla, mostrar estado/reintento, mantener lista/datos vigentes y retirar controles sobre una escena no disponible.
2. Contornos para todas las detecciones válidas; botón solo si enrichment_eligible; las demás son geometría no interactiva. Un registro compartido determina color/nombre sin afectar elegibilidad ni la identidad recibida.
3. Estado de foco/puntero independiente de selección, con prioridad contractual y limpieza en blur/pointerleave/cambio de fuente. Ningún hover crea peticiones ni cambia ficha.
4. Banda externa y leyenda en flujo. Todos los identificadores con white-space:nowrap; los nombres sí pueden envolver. Bordes y halos sin relleno ni glifos textuales sobre imagen. Mantener color de clase bajo estados.
5. Incluir pruebas con imagen anotada deliberadamente rotulada distinta del original para demostrar que se retiró la obstrucción integrada, no solo un span.

### Derivada visual

Un GET PNG nuevo recibe solo job/detection IDs y perfil permitido. El servicio valida dueño, trabajo completed/image, fuente vigente, detección coincidente y bbox_relative saneada; calcula el mismo ROI half-open que el recorte original de 006. Procesa solo esa región y devuelve bytes+metadata atómicos. La ruta no llama modelos y no acepta imagen, coordenadas, texto, rutas ni URL suministrados por el cliente.

El perfil display-contrast-v1 aplica gris, ampliación entera isotrópica 1..4 para aproximar alto >=64 cuando las cotas lo permiten y CLAHE(clipLimit=2,tileGrid=8x8), sin deskew ni padding. El escalado se reduce a un entero permitido si el límite de salida lo exige; si ni escala1 cabe, o el ROI tiene lado<2 o intensidad uniforme, responde no aplicable. PNG sin metadata de entrada. Ver límites/transformación en [data-model.md](data-model.md).

El comparador conserva Original como vista inicial; comienza preparación automática al seleccionar una placa válida. Ofrece Original/Procesada, ampliación local 1x/2x/4x dentro de un contenedor con scroll interno y leyendas persistentes. Alternar vista/zoom no modifica la lectura ni ejecuta modelos. La URL del procesado se retira al cambiar selección; no se crea historial de selección.

### Concurrencia, caché y timeout

La clave incluye dueño+fuente+job+detección+perfil/version. Se comparte solo el cálculo activo para la misma clave; las demás claves reciben 429 cuando el único cupo está ocupado. La caché admite hasta 8 entradas y 16 MiB de bytes+metadata; LRU elimina antes de exceder cotas. Expira en min(fuente,job), sin TTL deslizante. Regenerar una entrada ya expulsada es un cálculo nuevo permitido, nunca otra inferencia.

Ejecutar decodificación/transformación/codificación fuera del event loop, con deadline servidor de 8 s; medirlo desde admisión, no desde comienzo de CPU. Detectar desconexión y usar token cooperativo antes/después de cada etapa. Si todos los consumidores se retiran antes de terminar, no cachear/publicar. Una operación ya entregada puede permanecer en la caché temporal dentro del TTL y cotas. Timeout no libera cupo CPU hasta que el hilo termine; resultado tardío se descarta. Comprobar de nuevo autorización/TTL/estado bajo coordinación antes de cachear y antes de entregar; ningún lock envuelve la transformación.

En frontend, una única operación por selección con deadline monotónico <=10 s incluyendo headers/cuerpo/decode; TTL conocido puede acortarlo. Validar cabecera <=2048 bytes, esquema, identidad, perfil, ROI, transformación, tipo PNG y dimensiones antes de exponer Blob. 401/404/410 retiran evidencia afectada según lifecycle 006; 409/422/429/504 y otros fallos de tratamiento mantienen el original todavía autorizado y muestran recuperación explícita. No hay reintento automático de inferencia ni del GET tras timeout.

### Procedencia OCR y candidata

Añadir provenance opcional dentro de plate, normalizada antes de JSON/SQLite/respuesta. used_enhancement conserva su significado histórico de intento. selected_variant solo identifica texto publicado read; si no hay texto, none; históricos desconocidos no se reconstruyen. Preview profile describe una operación distinta, no la variante OCR.

baseline-v1 conserva exactamente el recorrido vigente. candidate-rescue-v1 se implementa para evaluación y permanece sin promoción por defecto; solo amplía un resultado baseline unreadable con dos variantes acotadas, nunca retoca una lectura baseline read. Video continúa usando la política previa. [evaluation-protocol.md](evaluation-protocol.md) fija recetas, reglas, dataset, métricas y decisión de promoción. Si no hay mejora suficiente, entregar comparación visual/evaluador no cierra US4 ni SC-006/009.

### Orden para generar tareas

1. Fixtures/contratos y geometría/procedencia: bloquean preview y comparaciones definitivas.
2. Registro/clases/contexto/escena limpia: US1/US2 independientes del procesamiento de placas.
3. Backend preview, caché/CORS/TTL, métricas, límites y pruebas de carreras antes de conectar el comparador.
4. Hook/comparador y pruebas de lifecycle/estados; preservar flujos de 006.
5. Congelar baseline, instrumentar provenance y candidatos solo para imágenes; pruebas de política y regresión de video.
6. Validación sintética, accesibilidad/píxeles/rendimiento de presentación; evaluación real reservada y promoción solo si supera su gate; documentar pendientes.

### Trazabilidad

| Alcance | Requisitos | Evidencia de cierre prevista |
|---|---|---|
| Escena/contexto/identidad | FR-001–004/008, SC-001/002 | 10 escenas, 3 densas >=21; IDs1/2/3 cifras; original/anotada distintos, teclado/toque/200% |
| Clases/estados | FR-005–008, SC-003 | Catálogo completo, colores únicos/estables, desconocida, contraste de control real |
| Original/procesada | FR-009–014, SC-004/007 | >=30 placas, identidad/ROI/metadata y comparación; p95 de selección a PNG decodificado |
| Sesión/recursos | FR-017–020, SC-005/008 | Expiry/cancel/late/401, single-flight, caché/cupo/deadline y health concurrente |
| Exactitud/procedencia | FR-014–016/019/020, SC-006/009 | Evaluación reservada >=60, errores/caracteres/lecturas falsas y reporte agregado |

## Validation strategy

- pytest: contratos anteriores/nuevo, saneamiento de provenance, ROI con bordes/EXIF/fracciones, rutas autorizadas, 404/410, origen no imagen, trabajo no finalizado, estado no read con bbox válido, límites, carrera al publicar/cachear, janitor y cierre.
- Frontend: prioridad de contexto, color estable, metadata inválida, deadline con body/decode bloqueados, igualdad de selección/ficha, reintento sin POST extra y URL revocada.
- Playwright: datos controlados y API real con adaptadores sintéticos; escena sin texto, contraste sobre blanco/negro, selección en tres viewports, original/procesada con fuente correcta, reset/late/cancel/expiry y video/conteo.
- Evaluación real: protocolo separado, original/candidata sobre mismo dataset/modelo/hardware, sin texto/imágenes/rutas en reportes públicos; no reemplazar por mocks.
- Esta fase valida documentos y contratos, no ejecuta la futura implementación ni afirma resultados de precisión/rendimiento.

## Complexity Tracking

Sin violaciones constitucionales. Una cabecera de metadata evita un endpoint descriptor y otro de imagen; no se añade cola persistente, tabla, servicio de superresolución ni dependencia gráfica de producción. El mecanismo acotado de RAM es necesario para no duplicar trabajo activo ni ampliar retención.

## Verificacion de esta planificacion

Se resolvio la plantilla activa y se revisaron los artefactos con dos investigaciones de solo lectura. Enlaces locales validos; 10 esquemas JSON Schema comprobados, todas las referencias locales resolubles/alcanzables y ejemplos de metadata/cliente anterior sin provenance validos. Se verifico no-store en respuestas correctas y errores y seguridad de las dos operaciones documentadas. La validacion de esquemas se ejecuto en un entorno temporal aislado, sin modificar dependencias del proyecto.

Los 191 archivos modificados/sin seguimiento presentes al cambiar de rama conservaron su hash y el indice quedo intacto; no se modifico codigo de aplicacion, spec.md ni documentos de006. No se ejecutaron inferencias, benchmarks ni pruebas de producto: son trabajo futuro. El siguiente paso es generar tasks.md; este plan no lo crea.
