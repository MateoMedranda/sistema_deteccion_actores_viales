# Data model — Iteración 006

## Identidades y referencias

- `SourceIdentity`: `(sessionGeneration, request_id)` en cliente; `(owner_key_id, source_id)` en servidor. `source_id=request_id` para imagen. Nunca asociar fuentes distintas por coincidencia de números.
- `DetectionIdentity`: `(request_id, detection_id)`, entero >=1 asignado una vez después de validar cajas. No renumerar al filtrar vehículos ni al paginar.
- `track_id`: null/ausente para imagen estática. No derivar de `detection_id`; referencia temporal real solo cuando la fuente la proporciona.
- `vehicle_key`: identificador existente de resultado, sin reemplazar la clave compuesta de detección. Un resultado debe pertenecer al job y fuente consultados.

## Imagen canónica temporal

| Campo | Regla |
|---|---|
| source_id, owner_key_id | Fuente y dueño existentes, sin exponer key_id al cliente. |
| original_path | Ruta privada que nunca se serializa. PNG canónico con orientación aplicada y RGB; no conserva EXIF/GPS. |
| width, height | Enteros >0 de los píxeles canónicos usados por detección, anotación y enriquecimiento. |
| media_type | `image/png` del recurso canónico; MIME/tipo y límites originales se validan antes de normalizar. |
| detections | Colección canónica inmutable; misma identidad/caja para anotación, respuesta y crop. |
| expires_at | Fecha UTC efectiva común a original/anotación/fuente o mínimo publicado explícitamente. No ampliar TTL al leer/reintentar. |

Nuevo descriptor público `original_image`: URL relativa protegida, `media_type=image/png`, `expires_at`. `source_expires_at` declara el límite de la fuente para la UI. No se crean copias por cada crop.

## Detección canónica

- `detection_id>=1`, `class_id>=0`, `class_name` no vacío, `confidence` entre 0 y 1.
- `bbox`: enteros, origen superior izquierdo, intervalos semiabiertos `[x_min,x_max) × [y_min,y_max)`.
- Invariantes: `0 <= x_min < x_max <= width`, `0 <= y_min < y_max <= height`.
- Truncar a enteros y limitar a la imagen según la misma política compartida; descartar degeneradas antes de asignar IDs, no forzar un píxel ficticio en una sola capa.
- `enrichment_eligible`: booleano calculado por el servidor con su conjunto de clases, no una lista rígida del cliente.
- La función compartida también se usa en recorte de video; probar que no cambia su política válida vigente.

## Estado cliente del recorrido

| Estado | Datos permitidos | Transición |
|---|---|---|
| idle / selected | Archivo/previsualización de sesión. | analyze -> detecting |
| detecting | Archivo, generación y controlador; sin resultados anteriores visibles. | éxito -> detected; fallo -> detection_failed |
| detected | Fuente, dimensiones, detecciones, vigencia y medios disponibles. | elegibles -> enrichment_submitting; ninguno -> empty/ready |
| enrichment_submitting | Mismos datos básicos; envío protegido de duplicación. | aceptado -> enrichment_queued; respuesta ambigua -> interrupted |
| enrichment_queued / enrichment_processing | Datos básicos, job_id y progreso real; secciones enriquecidas pendientes. | completed -> ready/partial; failed -> enrichment_failed; reset/TTL -> invalidated |
| ready / partial | Resultados validados e indexados por detección. Parcial = alguna rama ausente/fallida. | selección/reintento permitido según vigencia |
| detection_failed / enrichment_failed / interrupted | Error seguro; conservar solo evidencia vigente útil. | reintento explícito o nueva fuente; no rePOST automático ambiguo |
| expired / invalidated | Sin imágenes, recortes ni texto afectados. | nuevo análisis |

`selectedDetectionId` es único y no cambia por llegada de enriquecimiento. `AbortController`, timers y URLs no son parte de datos serializables. Al invalidar generación: cancelar esperas y limpiar inmediatamente; respuestas tardías se descartan. El registro de recursos revoca URLs en replace/reset/expiry/unmount.

## Enriquecimiento y ficha

- DTO de atributos y placa actuales: confianza 0–1, atributos independientes de placa.
- `plate.status`: read/unreadable/not_detected/failed. Texto permitido solo read; en todos los demás, `text=null` o ausente en cualquier representación.
- `plate.bbox_relative`: 0–1, orden estricto entre extremos; normalizado respecto al crop vehicular canónico, nunca la imagen completa.
- Placa localizada e ilegible o fallo de OCR: conservar bbox/localizer_confidence válidas y mostrar recorte original. Falta de localización no habilita recorte estimado.
- `VehicleView`: detección, estado de enriquecimiento, atributos, placa y referencias de evidencia. No contiene HTML ni respuestas crudas; error_code se traduce por catálogo seguro.
- `EvidenceCrop`: tipo vehicle/plate, identidad compuesta, caja válida y URL temporal. Solo generar para selección activa; revocar al cambiar. En pantalla, ajuste proporcional; tamaño de imagen no modifica coordenadas de origen.

## Trabajo y persistencia servidor

Estados existentes: queued -> processing -> completed/failed/cancelled; queued también puede cancelarse. Expired se representa por eliminación y respuesta 410 al dueño conocido, no se añade al enum persistido.

- `finish` y `fail` solo cambian desde processing vigente, mediante la misma transacción que valida el estado.
- Cancelar bajo bloqueo/transacción, borrar JSON y filas de resultados/candidatos relacionadas. Un worker tardío no vuelve a escribirlas.
- `processed_units` monotónico y <=total_units. Progresar incluso una unidad que termina con fallos; emitir un registro fallido con identidad en lugar de omitirla silenciosamente.
- Resultados se publican al completed; durante processing `results_ready=0`, resultados devuelve página vacía. Orden final determinista por detection_id para imagen; páginas 1..n con page_size 1–100 y total estable al finalizar.
- Normalización y validación única antes de JSON, tablas y respuesta. No almacenar secretos, imágenes ni rutas en resultados. No dar por seguro un JSON solo porque otra tabla esté redactada.
- TTL del job <=TTL fuente y límite de enriquecimiento. Janitor cada 1 s, eliminación de originales/resultados sin tráfico; tombstones mínimos por dueño para 410 sin texto o recortes.
- Ningún bloqueo cubre inferencia; comprobar estado/TTL entre unidades y antes de publicar. Una inferencia no interrumpible puede terminar internamente sin crear resultados visibles.

## Capacidad de enriquecimiento

`attributes`, `plate_localization`, `plate_ocr`: ready/unavailable según adaptador inicializado. `status=ready` solo si detección y todas las ramas están listas; si falta algo, `status=not_ready` y HTTP503 del endpoint de readiness existente, con capacidades por rama añadidas. No expone rutas, pesos ni mensajes de excepción.

Un readiness global negativo no prohíbe el trabajo parcial: se acepta si hay atributos o localización de placa útil, conservando recorte aunque OCR no esté disponible; si no hay ninguna rama útil, creación responde 503 seguro. Separar localización y lectura en el processor para preservar esa evidencia.

## Recursos y límites de privacidad

Sesión solo en memoria del navegador. Bytes originales de upload se liberan tras disponer del canónico; descriptor canónico reemplaza la previsualización de carga para geometría final. Backend guarda solo el original canónico ya necesario para enriquecimiento y las anotaciones temporales. Nuevo GET aplica propiedad, autorización y `Cache-Control: no-store`; datos ya entregados no son revocables físicamente, por lo que la UI debe retirar blobs al vencimiento y no exportar o persistirlos.
