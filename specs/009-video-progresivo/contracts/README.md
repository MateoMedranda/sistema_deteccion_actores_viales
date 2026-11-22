# Contratos — 009 Video progresivo

**Estado**: diseño aprobado para generar tareas; todavía no implementado. API aditiva en [openapi-additions.yaml](openapi-additions.yaml), tipos en [schemas.json](schemas.json) y ejemplos válidos en [examples.json](examples.json). Reglas de gateway en [gateway.md](gateway.md), reproducción en [player.md](player.md).

## Activación y compatibilidad

POST /api/v1/video-jobs?presentation=progressive conserva multipart video, API key e Idempotency-Key existentes y responde202 con VideoJobAccepted legacy. Sin query se mantiene el recorrido legacy. Un valor desconocido o repetido de presentation devuelve422. La huella de idempotencia debe incluir el modo; repetir el mismo intento devuelve el mismo trabajo, cambiar bytes/modo con la misma clave devuelve409.

No se modifica el significado de completed, processed-cfr, /detections, /summary, /annotated-video, conteo ni enriquecimiento final legacy. El cliente nuevo conoce su modo por su intención; consulta playback tras la aceptación. Trabajo legacy sin recurso progresivo responde404 a playback.

## Interfaces

| Método | Ruta bajo /api/v1/video-jobs/{job_id} | Resultado |
|---|---|---|
| GET | /playback | PlaybackState desde queued, aun sin cuadros; límite0 y source null hasta primer lote |
| DELETE | /playback | 204; retiro idempotente de este trabajo progresivo y sus derivados, incluso tras fallo/completado |
| GET/HEAD | /playback/source | MP4 original protegido; solo tras primer lote disponible, nunca URL externa |
| GET | /playback/frames | FramePage para ventana y snapshot; incluye vacíos y partes completas de observaciones |
| GET | /playback/tracks | TrackPage ligado al snapshot de enriquecimiento |
| GET | /playback/tracks/{track_id} | TrackResult más reciente, incluso pending; leer no inicia inferencia |
| GET | /playback/tracks/{track_id}/evidence/{evidence_id}/{kind} | PNG privado de vehicle o plate; no sustituye el plate-preview de imágenes |

Identificadores del trabajo conservan el formato existente de un segmento. generation y evidence_id son UUID opacos. track_id entero positivo real, no ordinal final detection_id. Todos los datos conservan job_id/generation y las revisiones correspondientes. Timestamps en microsegundos enteros seguros; intervalos de cuadro semia abiertos.

## Estado autoritativo

PlaybackState separa analysis_state, export_state y enrichment_state. available_until_us es extremo exclusivo del prefijo confirmado, no una estimación; last_frame_start_us permite volver al último cuadro sin solicitar el extremo exclusivo. frames_processed puede superar frames_published por el lote en vuelo. duration_us solo se presenta como definitiva con duration_confirmed=true.

source.url es relativa, emitida por servidor y coincide exactamente con la ruta de ese trabajo. media_available no debe ser true si no existe un prefijo consultable. expires_at no se amplía por polling, reproducción ni enriquecimiento.

## Ventanas y paginación

frames exige from_us>=0, to_us>from_us, ventana<=30.000.000us y snapshot>=0; este último se toma de revision del estado. to_us no supera el watermark de ese snapshot. cursor opcional, opaco, tamaño<=512 y vinculado a propietario/trabajo/generación/snapshot/ventana/continuación. Se rechazan claves desconocidas, duplicadas, números no finitos, negativos y cursores reutilizados en otro contexto.

Páginas <=1MiB, <=1.000 observaciones y <=100 fragmentos de cuadro. Si un cuadro requiere varias partes, observation_offset y observation_total permiten reconstruirlo sin truncar. FrameSlice con total0 y observaciones vacías confirma ausencia de vehículos. Cada observación tiene ordinal único en su cuadro. La ventana completa solo se admite después de agotar next_cursor y verificar continuidad, todas las partes e identidad. El rango solicitado puede cortar un intervalo: se devuelve el cuadro completo que lo intersecta, dentro del prefijo autorizado.

tracks usa snapshot=enrichment_revision y cursor de continuación; máximo100 unidades/página en orden discovery_ordinal estable. Revisión de resultados por unidad independiente. Los snapshots necesarios para paginar son inmutables durante la consulta; si un snapshot ya no puede resolverse se devuelve409 snapshot_stale y el cliente reinicia la lectura, sin inferencia. No se mezcla una mitad vieja con otra nueva.

## Errores, privacidad y ciclo de vida

- 401/403: autenticación o control de sesión rechazado; retirar evidencia afectada.
- 404: propietario ajeno o recurso desconocido, sin confirmar existencia. evidence no disponible tiene un estado explícito en la ficha y no queda pending indefinidamente.
- 409: interval_not_ready, snapshot_stale, cursor_context_mismatch o source_not_ready; es espera/recuperación, no revocación.
- 410: expiración o retirada conocida por el propietario. Se conservan solo tombstones mínimos durante la ventana operativa ya existente, no lecturas ni medios.
- 416: Range no satisfacible/inválido. 422: ventana, IDs, query o modo inválidos; 429 Retry-After; 503/504: indisponibilidad temporal sin inventar resultados.
- JSON y medios con Cache-Control:no-store; medios con CORP same-origin. Nunca rutas de disco, URL del backend ni secretos en respuesta/log.
- Fallo técnico congela el prefijo y conserva exclusivamente lo publicado y sus medios necesarios hasta TTL. Cancelación, limpieza, sustitución, rechazo y vencimiento retiran según spec; la respuesta tardía no resucita datos.
- DELETE devuelve204 también para un recurso propio ya retirado mientras exista su tombstone; un ID ajeno conserva404. Workers y lecturas comprueban retirada/TTL para evitar carreras.

## Ejemplos de comportamiento

Fuente120s, límite42s y posición18s: se admiten10s y30s, ir a42s muestra el último inicio de cuadro anterior al extremo, y60s se bloquea sin dibujar un cuadro pendiente. Al pasar el límite a55s la posición no se mueve. Fallo al segundo42 conserva ese tramo como parcial y permite consumir su cola aunque sea menor al margen de5s.
