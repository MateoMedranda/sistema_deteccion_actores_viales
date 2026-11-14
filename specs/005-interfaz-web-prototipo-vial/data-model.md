# Modelo de datos: Interfaz web prototipo vial

## Sesión de demostración

| Campo | Tipo | Regla |
|---|---|---|
| apiBaseUrl | URL HTTP(S) | Valor inicial http://127.0.0.1:8000; sin barra final; solo memoria. |
| apiKey | secreto opcional | Solo memoria; nunca se registra, serializa ni inserta en URLs. |
| activeImage | ImageResult opcional | Se sustituye al analizar otra imagen o reiniciar. |
| activeVideo | VideoJob opcional | Solo uno; cambiarlo exige cancelar o reiniciar. |
| activeCount | CountJob opcional | Asociado al video activo. |
| activeEnrichment | EnrichmentJob opcional | Asociado a imagen o video vigente. |
| objectUrls | conjunto temporal | Toda URL Blob debe revocarse al limpiar. |

## Trabajo remoto

| Campo | Tipo | Regla |
|---|---|---|
| id | UUID/cadena opaca | Solo se muestra mientras la sesión está activa. |
| kind | video, count o enrichment | Determina rutas de consulta, resultado y cancelación. |
| status | cadena del backend | Se conserva literalmente; estados terminales detienen polling. |
| progress | número opcional | Se muestra solo cuando el backend lo entrega. |
| expiresAt | fecha opcional | Al vencer, se limpia el resultado protegido y se informa el estado. |
| owner | implícito | Nunca se almacena ni calcula en frontend; el backend lo deriva de API key. |

## Línea de conteo

| Campo | Tipo | Regla |
|---|---|---|
| pointA, pointB | objeto x/y | Normalizados en [0,1], convertidos desde el rectángulo visible del video. |
| isValid | booleano derivado | Ambos puntos finitos, en rango y con distancia mayor que cero. |
| displayPoints | derivado | Se recalcula por tamaño del contenedor; nunca reemplaza puntos normalizados. |

## Resultado de imagen y medios protegidos

| Campo | Tipo | Regla |
|---|---|---|
| detections | lista | Clase, confianza y caja según contrato del backend. |
| artifactUrl | URL de objeto | Derivada de Blob solicitado con API key; no es URL remota persistida. |
| summary, events, results | listas paginables | Se muestran con páginas limitadas y estados vacíos seguros. |

## Resultado enriquecido

| Campo | Tipo | Regla |
|---|---|---|
| subjectId | detección o track_id | Es opaco y procede del backend. |
| attributes | atributos del backend | Se muestran sin inferencias locales. |
| plate.status | read, unreadable, not_detected o failed | Siempre visible como estado seguro. |
| plate.text | texto opcional sensible | Solo se muestra si estado read y backend lo entrega; se elimina al reiniciar/cerrar. |

## Transiciones de estado

```text
sesión vacía → configurada → carga/consulta → resultado temporal
                              ↓                  ↓
                           error seguro ← vencido/cancelado/fallido

video terminado + línea válida → conteo en cola/procesando → terminado/error/cancelado
fuente vigente                 → enriquecimiento en cola/procesando → terminado/error/cancelado
reiniciar → intenta cancelar activos → sesión vacía (sin esperar la respuesta)
```

