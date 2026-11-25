# Registro de evolución y fuentes para documentar el sistema

Actualizado: 2026-11-24. Checkout principal, rama feature/009-video-progresivo. Este índice conecta los registros versionados; no sustituye las especificaciones ni convierte comentarios del chat en requisitos aprobados.

## Dónde encontrar cada tipo de información

| Necesidad documental | Fuente |
|---|---|
| Requisitos y cambios aprobados | spec.md de cada iteración y sus enmiendas |
| Arquitectura, decisiones y alternativas | plan.md, research.md y data-model.md |
| Interfaces y restricciones de integración | contracts/ y OpenAPI generado por la aplicación |
| Trabajo previsto y realizado | tasks.md, con IDs y estado de cada tarea |
| Pruebas ejecutadas, resultados y límites | validation.md, audit.md y evidence/ |
| Instalación, arranque y uso | README.md del proyecto y quickstart.md de la iteración |
| Historial exacto del código | Commits Git y sus diffs |
| Sesiones de desarrollo y líneas de código | metricas/sesiones/*.csv |

Las métricas metodológicas de sesión (horas/LOC/causa de eliminación) describen el trabajo de desarrollo. Los FPS y latencias describen la ejecución del sistema: no son la misma medida. Consultar cada CSV como registro de sesión, sin asumir que equivale a la duración total de la conversación.

## Iteraciones disponibles

- **001-deteccion-imagen-vial** — Feature Specification: Detección vial en imagen: [spec.md](../specs/001-deteccion-imagen-vial/spec.md), [plan.md](../specs/001-deteccion-imagen-vial/plan.md), [tasks.md](../specs/001-deteccion-imagen-vial/tasks.md), [quickstart.md](../specs/001-deteccion-imagen-vial/quickstart.md).
- **002-procesamiento-video-vial** — Feature Specification: Procesamiento vial por video: [spec.md](../specs/002-procesamiento-video-vial/spec.md), [plan.md](../specs/002-procesamiento-video-vial/plan.md), [tasks.md](../specs/002-procesamiento-video-vial/tasks.md), [quickstart.md](../specs/002-procesamiento-video-vial/quickstart.md).
- **003-conteo-por-linea** — Feature Specification: Conteo de actores por línea: [spec.md](../specs/003-conteo-por-linea/spec.md), [plan.md](../specs/003-conteo-por-linea/plan.md), [tasks.md](../specs/003-conteo-por-linea/tasks.md), [audit.md](../specs/003-conteo-por-linea/audit.md), [quickstart.md](../specs/003-conteo-por-linea/quickstart.md).
- **004-extraccion-caracteristicas-y-placas** — Feature Specification: Extracción de características y placas: [spec.md](../specs/004-extraccion-caracteristicas-y-placas/spec.md), [plan.md](../specs/004-extraccion-caracteristicas-y-placas/plan.md), [tasks.md](../specs/004-extraccion-caracteristicas-y-placas/tasks.md), [audit.md](../specs/004-extraccion-caracteristicas-y-placas/audit.md), [quickstart.md](../specs/004-extraccion-caracteristicas-y-placas/quickstart.md).
- **005-interfaz-web-prototipo-vial** — Feature Specification: Interfaz web prototipo vial: [spec.md](../specs/005-interfaz-web-prototipo-vial/spec.md), [plan.md](../specs/005-interfaz-web-prototipo-vial/plan.md), [tasks.md](../specs/005-interfaz-web-prototipo-vial/tasks.md), [quickstart.md](../specs/005-interfaz-web-prototipo-vial/quickstart.md).
- **006-mejoras-frontend** — Feature Specification: Exploración visual de imágenes viales enriquecidas: [spec.md](../specs/006-mejoras-frontend/spec.md), [plan.md](../specs/006-mejoras-frontend/plan.md), [tasks.md](../specs/006-mejoras-frontend/tasks.md), [validation.md](../specs/006-mejoras-frontend/validation.md), [audit.md](../specs/006-mejoras-frontend/audit.md), [quickstart.md](../specs/006-mejoras-frontend/quickstart.md).
- **007-anotaciones-placas-legibles** — Feature Specification: Anotaciones despejadas y placas legibles: [spec.md](../specs/007-anotaciones-placas-legibles/spec.md), [plan.md](../specs/007-anotaciones-placas-legibles/plan.md), [tasks.md](../specs/007-anotaciones-placas-legibles/tasks.md), [validation.md](../specs/007-anotaciones-placas-legibles/validation.md), [audit.md](../specs/007-anotaciones-placas-legibles/audit.md), [quickstart.md](../specs/007-anotaciones-placas-legibles/quickstart.md).
- **008-exploracion-imagen-video** — Feature Specification: Exploración de imágenes y video: [spec.md](../specs/008-exploracion-imagen-video/spec.md), [plan.md](../specs/008-exploracion-imagen-video/plan.md), [tasks.md](../specs/008-exploracion-imagen-video/tasks.md), [validation.md](../specs/008-exploracion-imagen-video/validation.md), [audit.md](../specs/008-exploracion-imagen-video/audit.md), [quickstart.md](../specs/008-exploracion-imagen-video/quickstart.md).
- **009-video-progresivo** — Feature Specification: Video progresivo con navegación acotada y enriquecimiento: [spec.md](../specs/009-video-progresivo/spec.md), [plan.md](../specs/009-video-progresivo/plan.md), [tasks.md](../specs/009-video-progresivo/tasks.md), [validation.md](../specs/009-video-progresivo/validation.md), [audit.md](../specs/009-video-progresivo/audit.md), [quickstart.md](../specs/009-video-progresivo/quickstart.md).

## Cambios de rendimiento registrados en la iteración 009

| Cambio aprobado | Tareas | Commit de implementación | Evidencia/documentación |
|---|---|---|---|
| Perfil de tiempos por etapa y lector CLI | T107–T109 | 0107f73 | validation.md y quickstart.md |
| Detección cada dos cuadros y predicción intermedia | T110–T112 | af091cb | evidence/detection-interval-check.json |
| MP4 anotado solo al solicitar exportación | T113–T116 | 4a0638d | evidence/export-on-demand-validation.json |
| Fases internas de YOLO y este índice documental | T117–T120 | 3fbdee7 | evidence/detection-breakdown-check.json |

Se mantienen las identidades por trabajo y el conteo basado en observaciones confirmadas; se prueban ambas políticas de detección, reintentos y retirada. Las cajas intermedias son predicciones y no generan por sí solas evidencia OCR ni cruces confirmados. Consultar las enmiendas para el alcance exacto y sus límites.

## Mediciones reales ordinarias preservadas

Fuente versionada: [performance-history.json](../specs/009-video-progresivo/evidence/performance-history.json). Son tres ejecuciones completadas del usuario, con metadata equivalente; no una comparación alternada con carga del equipo controlada.

| Configuración observada | Tiempo total | FPS de análisis |
|---|---:|---:|
| Todos los cuadros + video automático | 10 min 25 s | 6,100 |
| Intervalo 2 + video automático | 7 min 35 s | 8,482 |
| Intervalo 2 + sin exportación | 5 min 42 s | 10,571 |

El último cambio redujo el tiempo total observado un 25.0 %; la reducción acumulada respecto al primer caso fue 45.3 %. Los FPS excluyen conversión final y el tiempo total la incluye cuando existía. No atribuir cada variación de una etapa exclusivamente al código ni deducir calidad del detector a partir de tiempos.

## Perfiles operativos y conservación de evidencia

Los informes originales de ejecución permanecen en backend/.runtime/video-profiles/ y las exportaciones en video-export-profiles/, junto a la base de datos configurada. No se suben a Git como historial automático. Las comparaciones utilizadas en documentos deben conservarse como agregados revisados en evidence/, con contexto, configuración y límites; nunca copiar .env, claves, videos, matrículas o recortes privados al repositorio.

El informe versión 2 añade detection_breakdown. Las fases nativas ya forman parte del tiempo de detección: no sumarlas otra vez. Registrar cobertura e incidencias; el tiempo sin atribuir puede incluir trabajo del modelo no medido cuando faltan datos. Los informes antiguos no contienen ese desglose.

## Pendientes y criterio para redactar documentos

Las comparaciones largas AB/BA, la evaluación exhaustiva de calidad/memoria/navegadores y la prueba de uso con cinco personas mantienen el estado indicado en tasks.md/validation.md. No presentar diagnósticos breves, pruebas sintéticas o mediciones ordinarias como aceptación de esos requisitos.

Para cada futura sección del documento del sistema: citar el requisito/decisión vigente, el ID de tarea, el commit y la evidencia real que la respalda. Conservar resultados fallidos y limitaciones; usar el código y contratos actuales para describir el estado implementado y las enmiendas para explicar su evolución.

## Control de hilos CPU — 2026-11-24

T121–T124 incorporan TORCH_NUM_THREADS en backend/.env y telemetría de hilos efectivos. Referencias: enmienda de plan.md, instrucciones en quickstart.md y diagnóstico agregado evidence/cpu-thread-check.json dentro de specs/009-video-progresivo. La selección CPU de Ultralytics activa fijaba 8 intra-op; el diagnóstico aislado también observó 8 inter-op. La configuración local explicita 8 y permite ensayar otros valores reiniciando la API. No se cambian pesos, umbral, entrada, intervalo, conteo, exportación ni runtime.

Medición ordinaria completa 94d2c465-2c0d-49ce-81fc-39807fb882f9: 3611 cuadros, 266774.502 ms de análisis, aproximadamente 13.536 FPS; inferencia nativa 101.249 ms por llamada, 96.245 % de detección y aproximadamente 68.54 % del análisis. El perfil anterior no registra hilos; el 8 se verifica sobre la selección CPU de la misma instalación, no mediante introspección del proceso histórico. Instrumentar fases no acredita una mejora de ejecución.

El diagnóstico breve compara procesos nuevos con 8/1/2/4/16/8 hilos, 24 cuadros fuente iguales, intervalo 2 y tres llamadas de calentamiento por proceso. Las 12 detecciones medidas por proceso registran el valor solicitado sin discrepancias. Los tiempos de inferencia fueron 81.390/377.807/233.198/137.542/83.828/87.315 ms por llamada. Repetir 8 al final muestra variación de la medición; 16 no demuestra una ventaja clara sobre 8. Todos conservaron clases, IDs y cajas enteras en este tramo; no es una evaluación exhaustiva ni una medida de FPS del pipeline. Se conservan solamente agregados, contexto y resultado de comparación, sin cuadros, rutas de medios ni datos de reconocimiento.

Edge computing describe dónde se ejecuta, no un rendimiento garantizado. Cámaras con acelerador neuronal y modelos compatibles/optimizados pueden tener un comportamiento distinto a este proceso PyTorch en CPU. No hay evidencia de que este checkpoint YOLOv10s concreto mantenga 30 FPS en una cámara determinada. Referencias: https://docs.pytorch.org/docs/stable/notes/cpu_threading_torchscript_inference.html y https://www.raspberrypi.com/products/ai-camera/.

## Iteración 010: ficha, evidencia temporal y cruces dirigidos — 2026-11-24

Especificación: [010-video-detalle-conteo](../specs/010-video-detalle-conteo/spec.md). Checklist: [requirements.md](../specs/010-video-detalle-conteo/checklists/requirements.md). Se crea desde el estado actual del checkout principal (main, con base 54f615c) en feature/010-video-detalle-conteo y se conservan los archivos previos.

Requisitos: ficha de video consistente con imágenes sin scroll vertical anidado de toda la ficha; recortes/enriquecimiento vinculados al instante seleccionado y estables frente a actualizaciones; exportación explícita con etiquetas de clase e identidad; cruces reales del segmento en un único sentido elegido con flecha; resumen final por clase independiente del conteo. La decisión de sentido fue confirmada expresamente por el usuario. Los conteos usan identidades locales, con límites de seguimiento documentados.

Esta entrega es únicamente specify: cinco historias, 24 requisitos, nueve criterios de éxito y checklist de calidad. No implementa capacidades, no acredita pruebas de producto ni cierra pendientes anteriores; plan, tareas y validaciones posteriores deben conservar la trazabilidad y sus commits. La evaluación de aceleración AMD queda fuera de esta iteración.

### Planificación de010 — 2026-11-24

Artefactos: [plan](../specs/010-video-detalle-conteo/plan.md), [investigación](../specs/010-video-detalle-conteo/research.md), [modelo de datos](../specs/010-video-detalle-conteo/data-model.md), [contratos](../specs/010-video-detalle-conteo/contracts/README.md), [guía de validación](../specs/010-video-detalle-conteo/quickstart.md) y [validación documental](../specs/010-video-detalle-conteo/design-validation.md).

Decisiones: inspecciones inmutables por fotograma y extracción PTS exacta bajo demanda; ficha compartida sin scroll completo; conteo dirigido de segmento finito con revisión/eventos históricos; inventario de identidades por votos de clase independiente de OCR/línea; exportación explícita vehicle-labels-v1, sin reutilizar MP4 antiguos como etiquetados. Se mantienen APIs legacy, modos de detección, hilos, pesos y runtime. La clasificación consolidada puede diferir de la etiqueta observada de un cuadro; identidades locales no garantizan vehículos físicos únicos tras perder seguimiento.

Revisión documental:16 esquemas,8 ejemplos válidos y8 negativos,37 referencias y13 operaciones verificadas; no son pruebas de implementación. Se generarán tareas en la siguiente fase. La sesión de planificación registra esfuerzo metodológico y cambios confirmados, no FPS ni exactitud del sistema.

### Tareas de010 — 2026-11-24

Artefactos: [tasks.md](../specs/010-video-detalle-conteo/tasks.md), [puntos-tarea.csv](../specs/010-video-detalle-conteo/puntos-tarea.csv) y [validación de generación](../specs/010-video-detalle-conteo/task-generation.md). Se generan74 tareas pendientes: US1=7, US2=18, US3=14, US4=11, US5=10, más14 de setup/fundamentos/cierre. Incluyen12 oportunidades de paralelismo acotadas por dependencias y archivos; MVP visual T001–T015. B1–B5 se trazan a sus historias y al cierre transversal.

Formato/dependencias y cobertura de24 FR/9 SC comprobados; restricciones del modelo de datos y pruebas previstas incluidas. Hook de puntos revisado/recalculado:399 PTS de línea base, sin clasificaciones heurísticas pendientes. No son horas ni rendimiento del sistema. Sin implementación ni pruebas de producto en esta fase; continúa analyze. La sesión metodológica y sus commits conservan trazabilidad separada de métricas operativas.

### Corrección documental de010 — A1/U1 — 2026-11-24

Se aclaran las clases elegibles del conteo y su evaluación en la medición confirmatoria, conservando el evento histórico frente a cambios posteriores de clase. T001 creará el comparador sintético y capturará la referencia antes de cambios de producto; T071 comparará contra esa referencia sin sobrescribirla. Detalle y límites: [remediation.md](../specs/010-video-detalle-conteo/remediation.md).

Se mantienen 74 tareas y la cobertura de 24 FR/9 SC. El recálculo es 402 PTS por ampliar T001 de documentación a prueba de rendimiento; se conserva el antecedente de 399 PTS. No se ejecuta implementación ni comparación larga y los entregables de evidencia siguen pendientes de sus tareas.
