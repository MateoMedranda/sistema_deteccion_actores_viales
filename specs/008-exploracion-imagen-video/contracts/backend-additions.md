# Contratos aditivos de backend —008

Se conservan endpoints, autenticación X-API-Key/Principal y estados de002/004/006/007. Los siguientes son destinos de implementación, no cambios ya ejecutados. Esquemas: [schemas.json](schemas.json).

## GET /api/v1/web-policy

Nuevo endpoint protegido con require_api_key; delega en WebPolicyService, sin cargar modelos ni crear trabajos.200 WebPolicy devuelve:
- image: media_types y límites max_upload_bytes/max_image_pixels vigentes.
- video: media_types y límites max_upload_bytes, max_duration_seconds, max_width/height, max_fps/frames vigentes.
- capabilities: image_detection/video_analysis/attributes/plates, booleanos de disponibilidad.
No incluye URL privada, claves, nombres de pesos/rutas, propietario o Settings.401/503 usan ErrorResponse seguro. Cabeceras no-store. Se devuelve200 con capacidades falsas si la conexión está autorizada pero un modelo no está listo; eso no acredita disponibilidad de inferencia.

## GET/DELETE /api/v1/video-jobs/{job_id}

Conservar VideoJobResponse/status y añadir los campos de VideoJobAdditions. Nuevas ejecuciones siempre publican fase coherente:
queued -> frames -> encoding -> publishing -> ready.
- queued corresponde a status queued.
- frames/encoding/publishing corresponden a processing.
- ready solo con completed/metadata confirmada.
- failed/cancelled son terminales y no publican un resultado tardío.
- registros históricos pueden tener fase/metadata null; se usan estados históricos sin inventar precisión temporal.

processed_frames cuenta cuadros realmente leídos/escritos, no se fuerza al total de ffprobe. total_frames es estimado hasta EOF; luego se confirma/corrige al conteo real y frame_total_confirmed=true. progress_percent histórico es porcentaje saturado0..100 de cuadros, no finalización integral. Durante encoding/publishing la UI usa estado indeterminado, aunque el campo histórico sea100. No se cambia su tipo/rango.

Al completar, video_metadata describe el MP4 CFR: width/height/fps/frame_count/duration_seconds/timebase. eligible_track_count se calcula desde raw con las clases elegibles del servidor; classes_present contiene nombres únicos de todas las clases. No usar summary.detections como número de vehículos: sigue contando observaciones por cuadro.

El janitor debe entregar las rutas purgadas al servicio de artefactos, sin perder referencias al eliminar filas. Los recursos en uso quedan bajo su dueño activo hasta cierre seguro; el worker retira parciales y el janitor reintenta eliminación, sin publicar ni ampliar TTL. Probar Windows y ausencia de archivos huérfanos tras cancelación/expiry/cierre.

Migraciones SQLite con PRAGMA/ALTER idempotentes para processing_phase, actual_frame_count y columnas de idempotencia. INSERT de columnas explícitas en código/fixtures. Los objetos históricos sin conteo confirmado no adquieren un video_metadata inventado. La metadata pública nunca incluye paths.

## Publicación y proceso externo

Procesar todo cuadro como antes, almacenar FrameDetection raw y dibujar PresentedBox efímera. No alterar detector/tracker/thresholds, selección de evidencia o geometría del conteo. Video de análisis limpio; el artefacto de conteo mantiene su línea/totales003, sin reintroducir rótulos vehiculares.

Mismo encoder H264 y parámetros aprobados. Sustituir subprocess.run no cooperativo por supervisor Popen: -nostdin, salida descartada/buffer acotado y sin logs de paths; sondeo<=50ms de cancelación/TTL/plazo. Presupuesto=min(60s de codificación, tiempo restante del deadline vigente del job). No aumentar video_job_timeout_seconds para pasar gates.
Al cancelar/vencer: terminate, esperar1s y kill si sigue activo; retener el cupo hasta reap efectivo. Limpiar raw.mp4 y salida no publicada. Cancelar marca estado y solicita retiro; el worker que posee archivos/procesos realiza la limpieza segura, sin borrar un archivo abierto desde el HTTP ni bloquear el event loop.

finish publica archivo+raw observaciones bajo lock/transacción solo si sigue processing y vigente. Devuelve completed/cancelled/expired/failed efectivo. Ningún timeout/retiro libera worker mientras el hilo/proceso real siga activo. Recuperación de processing tras reinicio elimina parciales propios y reinicia su fase, sin mezclar detecciones anteriores. Métricas se emiten según desenlace efectivo, sin excepciones/rutas/medios/textos sensibles.

## POST /api/v1/video-jobs y POST /api/v1/enrichment-jobs

Añadir Idempotency-Key opcional16..128 [A-Za-z0-9_-], conservando comportamiento actual sin header. Autenticar antes de aceptar upload. CORS directo añade únicamente Idempotency-Key a headers permitidos, conservando orígenes/métodos/autenticación.

Almacenamiento: idempotency_key_hash y request_fingerprint nullable en filas de ambos stores, índice UNIQUE parcial(owner_key_id,idempotency_key_hash). Fuente, propietario y TTL se validan antes de replay. Tras las guardas de entrada y autorización, mismo fingerprint retorna202 con el recibo original y sin otra cola/inferencia; otro payload válido devuelve409 idempotency_conflict. Los errores de entrada conservan su precedencia y códigos previos. No cambiar created_at/expiry ni deduplicar indefinidamente después de purgar el job.

Fingerprint de upload = SHA256(MIME normalizado + byte nulo + bytes originales). Validación/escritura bajo límites existentes, hash incremental, sin incluir filename/path. Dos cargas simultáneas pueden validar copias, pero la transacción admite una sola fila; replay/conflicto borra únicamente el staged extra. Enriquecimiento usa JSON canónico {kind,source_id}, sin datos de placa. Una nueva tentativa explícita después de fallo conocido usa clave nueva; no crear otra mientras el resultado de aceptación sea incierto.

El recibo status=queued significa estado de admisión original; NO representa estado actual en un replay. La UI siempre hace GET inmediatamente después del recibo antes de afirmar fase/progreso. Preservar VideoJobAccepted/EnrichmentJobAccepted y sus esquemas históricos.

La garantía dura hasta TTL original de la fila; los clientes administrados no reenvían intenciones vencidas. No crear tabla permanente, historial, deduplicación por contenido entre operadores ni un endpoint de recuperación de usuarios.

## Enriquecimiento y resultados

POST video usa source.kind=video y el videoJobId vigente; sigue409 antes de completed,400 no_eligible_vehicles y503 si no hay capacidades. El encadenado de UI empieza tras video ready; eligible_track_count=0 evita crear un trabajo inútil. La carrera400 también se traduce a no aplicable.

Mantener los límites de workers/cola, máximo de evidencia por track y política de video actuales. Ningún zoom/pausa/lista busca nuevos cuadros ni vuelve a inferir. DELETE enriquecimiento no elimina un video ya terminado. Un retry solo reutiliza fuente mientras su original/vigencia lo permiten.

GET resultados conserva paginación1..100 y los campos existentes:
- track_id local al video; detection_id no es ID de trayectoria.
- evidence_frame_indexes en resultado/placa y evidence_frame_index por atributo.
- provenance opcional existente; no reconstruir el origen a partir de used_enhancement.
No se añaden crops de video ni endpoints temporales de contornos. La ficha textual es válida cuando no hay medios adicionales autorizados.

## Pruebas de contrato previstas

Autenticación temprana, permisos/dueño, null históricos, fase100 antes de codificar, conteo real, EOF, cancel/TTL durante FFmpeg y justo al publicar; recibos concurrentes/replay/conflicto/timeout; source elegible/no elegible; CORS/no-store; conservación de API anterior, count y política OCR. Tests de extracción de metadatos sin filesystem en rutas HTTP: servicios/stores/adaptadores mantienen responsabilidades.
