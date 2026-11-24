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
