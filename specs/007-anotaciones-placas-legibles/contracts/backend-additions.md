# Contrato aditivo de backend — 007

Las operaciones de detección, original, anotada, enriquecimiento, video y conteo vigentes permanecen compatibles. Implementado en 007; validación técnica y estado de aceptación real en ../validation.md. OpenAPI de la nueva ruta y tipos aditivos en [openapi-additions.yaml](openapi-additions.yaml).

## GET /api/v1/enrichment-jobs/{enrichmentJobId}/detections/{detectionId}/plate-preview

Autenticación X-API-Key mediante Principal existente. Único parámetro de consulta profile=display-contrast-v1 (valor por defecto). No acepta cuerpo, coordenadas, texto, URL de origen, rutas ni receta arbitraria. No crea nuevo job persistido, no realiza inferencias y no prolonga TTL.

Resolver job y fuente por mismo dueño; completed/image, resultado por detection_id y clase coincidente, track_id null y bbox_relative saneada. Permitir read/unreadable/failed con bbox válida, rechazar not_detected. Usar original canónico y ROI entero conforme a [data-model.md](../data-model.md); sin aproximaciones ni cuatro esquinas inventadas.

Respuesta 200: image/png, Cache-Control:no-store y X-Plate-Preview-Metadata obligatoria. Header = JSON ASCII compacto <=2048 bytes, con version/source_id/enrichment_job_id/detection_id/profile_id/input_size/output_size/original_bbox/applied_steps/original_to_processed/expires_at. No contiene texto de placa, clave ni ruta. PNG sin EXIF/texto heredado. Es un derivado, no un reemplazo del original.

Exponer en CORS únicamente la nueva cabecera además de las existentes: expose_headers=[X-Plate-Preview-Metadata]; mantener orígenes autorizados, allow_credentials=False, métodos y autenticación. La clave nunca viaja en URL.

## Errores

Formato ErrorResponse vigente: code,message segura,request_id; nunca traceback, rutas o contenidos OCR.

| HTTP | code | Semántica |
|---|---|---|
| 401 | invalid_api_key | Autenticación rechazada; no esperar cuerpo para retirar evidencia |
| 404 | job_not_found / source_not_found / detection_not_found | Recurso ajeno o desconocido, sin revelar propietario/existencia |
| 410 | job_expired / source_expired | Recurso vencido del dueño conocido |
| 409 | preview_source_not_ready | Job propio no completed o source_kind distinto de image |
| 422 | plate_not_applicable | Sin bbox/original suficiente, ROI degenerado/plano/lado<2, cotas del perfil no aplicables |
| 422 | invalid_request | ID/parámetro de perfil inválido, sin aceptar recetas arbitrarias |
| 429 | plate_preview_busy | Cupo activo ocupado por otra clave; Retry-After:1, sin encolar |
| 504 | plate_preview_timeout | Superado deadline de cómputo, sin entregar ni cachear resultado tardío |
| 503 | plate_preview_unavailable | Fallo seguro de decodificación/transformación/codificación |

Todas las respuestas, incluidos 401/404/410/422/429/503/504, llevan Cache-Control:no-store. En todo error no se devuelve PNG ni metadata ready. Rechazos de acceso/TTL siguen el lifecycle de 006; el resto conserva el original todavía autorizado. El endpoint no usa 404 para indicar simplemente que no se detectó una placa: ese caso es 422.

## Presupuesto y almacenamiento

Servidor: 8 s desde admisión. Cliente: <=10 s total incluyendo cuerpo y decode, acortado por TTL. Un solo cálculo por proceso; single-flight por dueño+fuente+job+det+perfil. Caché RAM LRU8/16MiB, PNG<=2MiB, lado<=2048 y <=2Mpx. No ampliar límites de entrada ni cambiar parámetros del modelo por estas cotas.

Revalidar acceso antes de leer, en cache hits y antes de publicación/entrega. Ningún bloqueo cubre decodificación/transformación. Token cooperativo entre etapas; sin consumidores pendientes no publicar. Mantener permiso CPU hasta terminar hilo real tras desconexión/timeout para evitar sobreconcurrencia. Si ya se entregó válidamente, conservar temporalmente bajo TTL/cotas hasta expulsión. Cleanup <=2 s y close coordinado, sin archivos derivados en disco.

Registrar plate_preview con request_id/job_id/source_type=image, profile_id permitido, duración y RSS inicial/final/máximo, resultado/error seguro. No introducir detection_id/imagen/texto como etiquetas arbitrarias de métricas externas. Mantener desenlace atómico T083: medir abandoned/expired/failed conforme al resultado real.

## Extensión de EnrichmentPlate

Campo provenance opcional/null, tipado conforme a PlateReadingProvenance007. Nuevas imágenes usan metadata exacta; datos antiguos sin campo se representan con origen desconocido, no se adivina a partir de used_enhancement. El booleano previo mantiene significado de tratamiento intentado.

Validación: selected_variant read pertenece a attempted_variants; sin read, selected_variant none y text=null. Legacy-unknown permite unknown/lista vacía. La normalización sanea todas las representaciones antes de SQLite/JSON/respuesta, conservando bbox válida si OCR falla. No guardar textos descartados; no nueva tabla ni migración que fabrique procedencia. selected_variant describe texto publicado, profile_id del preview describe solo visualización.

La política candidate-rescue-v1 permanece experimental hasta superar SC-006 mediante evaluation-protocol.md. El servidor normal compone baseline-v1 por defecto; ninguna petición de usuario, flag de interfaz o elección de vista puede activar una candidata no validada. La promoción, si procede, será un cambio explícito de composición/configuración acompañado de reporte; el video conserva política previa.

## Verificación contractual exigida

Validar OpenAPI documentado y generado, referencias locales, seguridad de la ruta, header obligatorio/limite/esquema, CORS real y errores JSON. Añadir pruebas de cliente antiguo y campos nuevos ausentes, geometría/identidad, acceso ajeno, TTL entre etapas/cache/entrega y cancelación. Una cabecera presente por sí sola no acredita un PNG correcto: cliente comprueba MIME, bytes, decode y dimensiones.
