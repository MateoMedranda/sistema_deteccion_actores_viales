# Contratos de diseño: Video 010

Estado: propuestos, no implementados. [openapi-additions.yaml](openapi-additions.yaml), [schemas.json](schemas.json) y [examples.json](examples.json) describen las interfaces nuevas; [ui.md](ui.md) describe interacción. El OpenAPI es una adición: en /export renderer es opcional; omitirlo conserva el contrato histórico y seleccionarlo activa la variante etiquetada. La respuesta documenta ambas formas sin exigir renderer a clientes existentes. El diseño de recursos está en [data-model.md](../data-model.md).

## Reglas comunes y compatibilidad

- Base API `/api/v1/video-jobs/{job_id}/playback`; navegador usa `/web-api` delante y sesión/CSRF del gateway. La API mantiene X-API-Key y propiedad. Autenticación HTTP existente sin cambios; no enviar claves al navegador.
- JSON cerrado, sin propiedades/query desconocidas ni parámetros duplicados; IDs de trabajo existentes, UUID de generación/contexto/assets, enteros seguros0..2^53-1 y track>=1. Rechazar bool donde se espera entero y valores no finitos; puntos distintos y bbox de área positiva dentro de fuente.
- JSON de control <=64KiB, respuesta de estado<=1MiB; las cuotas de contextos/bytes son del modelo de datos. Sin URLs, paths, píxeles, bbox, propietario o texto OCR en solicitudes de creación.
- Cache-Control:no-store, CORP:same-origin en medios, TTL del padre como máximo; reiterar propiedad/retirada antes de publicar y por bloque de streaming. Los medios usan rutas relativas emitidas por servidor, asset_id inmutable y ETag que incorpora generación/asset o versión, no solo tamaño.
- Las rutas /summary, /playback/count y /tracks/{id}/enrich conservan semántica y respuestas previas. PlaybackState/FrameSlice cerrados no reciben campos nuevos para evitar romper lectores estrictos. Las capacidades se consultan aparte.
- 401/403 de sesión retiran según el flujo vigente; 404 oculta recursos ajenos. 404 de inspección/asset propio no supone retirar todo el video: la ficha muestra fallo local. 410 del padre obliga a retirar todos sus derivados del cliente.

## Matriz de interfaces

| Método | Ruta relativa a playback | Resultado |
|---|---|---|
| GET | /capabilities | 200 Capabilities sin efectos; describe capacidades verificadas del trabajo |
| POST | /inspections | 202 Inspection; creación/dedup y encolado acotado |
| GET | /inspections/{inspection_id} | 200 Inspection; estado/resultado del contexto fijo |
| GET | /inspections/{inspection_id}/assets/{asset_id}/{kind} | PNG vehicle/plate congelado y privado |
| GET | /inspections/{inspection_id}/plate-preview?profile=... | PNG visual del mismo plate con metadatos de política existente |
| PUT | /directed-count | 200 DirectedCount; aplica línea/sentido con revisión esperada |
| GET | /directed-count?generation=...&revision=...&at_us=... | 200 DirectedCount histórico; revision opcional, generation obligatoria |
| DELETE | /directed-count?generation=...&expected_revision=... | 204, desactiva con control de concurrencia |
| GET | /detection-summary?generation=... | 200 DetectionSummary, independiente de playhead/línea |
| GET/POST | /export?renderer=vehicle-labels-v1 | 200/202 LabelExportStatus de esa variante |
| GET/HEAD | /export/content?renderer=vehicle-labels-v1 | MP4 etiquetado listo, 200/206/416 conforme al guard de Range |

## Inspección temporal

POST cerrado `{generation,track_id,frame_index}`. El cuadro debe estar en el prefijo confirmado y contener esa identidad. El servidor resuelve PTS/base temporal, start/end, clase y raw_bbox del recibo. Una selección predicha conserva el cuadro y declara observation_kind=predicted; no fabrica medición ni vuelve a detectar escena. Parámetros de política se fijan en servidor, no se aceptan por request.

La clave única incluye generación, identidad, índice y selected-frame-v1. Repetir POST, incluso tras perder respuesta, devuelve el mismo inspection_id, crop y resultado terminal válido sin repetir trabajo. Un frame diferente crea un contexto distinto aunque sea el mismo Track ID. Crear no exige que hayan terminado todos los vehículos o el análisis completo. La API devuelve202 rápidamente tras validar/reservar, nunca mantiene abierta la petición mientras ejecuta OCR.

Estado queued/preparing puede carecer de crop; processing publica un vehicle asset estable mientras completan atributos/placa. ready/partial/failed/not_applicable son terminales; unavailable expresa correspondencia/evidencia no obtenible. Ningún estado posterior reemplaza un vehicle asset publicado. Todos los atributos/placa apuntan a inspection_id; plate_asset debe proceder del mismo vehicle crop y no de otro candidato temporal. Las revisiones de resultados no son claves de caché de imagen.

Si faltan observación/fuente/correspondencia se explica el contexto no disponible; no se usa evidence[0] legacy. Alternativas temporales pueden consultarse desde observaciones/recursos existentes y se convierten en otra selección explícita y otro POST; no hay salto automático de tiempo. Un contexto terminal fallido no se vuelve a encolar por polling. La expiración se fija al primer POST aceptado; una vez vencida, el mismo contexto devuelve410 inspection_expired sin recreación. Conservar solo clave de dedup/ID/expiración hasta TTL padre; estos recibos cuentan para las128 admisiones del job, sin conservar resultados ni imágenes. La cuota de bytes se libera al borrar assets, la de admisiones al retirar el padre. Cierre de ficha cancela entrega en navegador, no crea ni retira trabajo arbitrario del servidor.

El GET de estado no decodifica ni inicia modelos. El GET de plate-preview aplica únicamente una transformación visual acotada del PNG congelado según perfiles admitidos del servicio existente; no cambia original/OCR, respeta cuota y puede reutilizar caché derivada. `plate_preview_url` es null hasta que exista placa; perfiles disponibles se anuncian en la inspección. Perfil inválido422, placa pendiente409, ausencia definitiva404 local; cabecera X-Plate-Preview-Metadata contiene el DTO nuevo InspectionPlatePreviewMetadata (`version=inspection-plate-preview-v1`), con contexto de video/asset, espacio plate-crop y afín original→procesada. Requiere parser de video; conservar intacto el DTO/parser de imágenes y no fabricar sus IDs. Permite comparar original/procesada sin confundirlo con una nueva lectura.

## Conteo dirigido

PUT cerrado `{generation,expected_revision,line:{point_a,point_b},direction}`. Dirección obligatoria negative_to_positive|positive_to_negative; ambos/both no es válido. Rev0 representa ausencia de configuración previa. Primera creación produce rev1; misma configuración con revisión vigente no reinicia; cualquier expected_revision obsoleta409 count_revision_stale. Tras respuesta perdida, GET permite verificar si el cambio ya está aplicado antes de reintentar. DELETE requiere misma disciplina y deja revisión desactivada; si ya está disabled y la revisión coincide, no cambia otra vez.

La flecha atraviesa el segmento siguiendo su normal en píxeles fuente. A/B nombran extremos, no sentidos. Usar únicamente centros raw medidos y segmento inclusivo; predicciones no actualizan el estado. Fecha de evento=medición que confirma el paso. Cada identidad se cuenta como máximo una vez por revisión. Una pasada inversa/exterior no consume elegibilidad para un cruce correcto posterior. Regla de contacto/on-line en research R5 y data-model.

GET solo lee: generation debe coincidir; revision si se incluye debe ser la activa, o409. `0<=at_us<available_until_us`; el cliente usa el cuadro pintado o last_frame_start_us, no el extremo exclusivo. Con prefijo vacío solo at_us=0 devuelve pending/null (o disabled/0), sin afirmar cobertura. Watermark del análisis y covered_until_us del reducer se distinguen. Ready requiere `at_us<covered_until_us`: en igualdad puede faltar un evento fechado justo al empezar el siguiente cuadro. Cuando existe cobertura estricta, status ready y total entero; cuando aún no, status pending y total=null, nunca el total final del futuro. Disabled devuelve total0 y geometría/dirección null. Un reducer puede estar atrasado solo para el último tramo y dar ready para posiciones anteriores cubiertas. Consulta repetida no inserta eventos ni avanza el cursor.

Aplicar nueva configuración encola reconstrucción acotada del prefijo medido existente, no una nueva detección/decodificación. El estado pending permite visualizar progreso de cobertura. Cambiar línea/sentido no toca inventario ni p_count legacy. Datos viejos con procedencia insuficiente: unavailable y motivo seguro, no cruce inventado.

Elegibilidad del contador: La elegibilidad de cruce se evalúa únicamente con la clase medida en la observación que confirma el paso, normalizada con strip/lower. Se admiten car, truck, bus, van, pickup, suv, sedan, hatchback, mpv, estate, bicycle y motorcycle; person, vacío y clases no catalogadas no suman cruces. Todas las mediciones conservan el estado geométrico de la trayectoria; un paso excluido por clase no consume la elegibilidad para un futuro cruce válido. Guardar class_key_at_crossing inmutable en el evento y no reevaluarlo con votos futuros, clasificación consolidada u OCR. Esta política no restringe el resumen: sus clases no catalogadas siguen visibles con requires_review. No se añade query/body para cambiar clases; la política está fijada en finite-center-v1.

## Resumen de identidades por clase

GET exige generation, no acepta posición ni línea. Estado building mientras el inventario se pone al día; partial al conservar prefijo de un trabajo no completado; final solo con análisis completo y cobertura íntegra; unavailable si no se puede acreditar procedencia. `total_tracks=null` para unavailable; building/partial reportan únicamente identidades confirmadas de su cobertura. Revisiones futuras pueden cambiar clase/total mientras sea parcial; no presentar como definitivo.

Ganador por votos reales, confianza máxima y clave lexicográfica, en ese orden. Cada identidad aporta exactamente una unidad a su clase consolidada. Clases conocidas incluyen bicicleta y moto; person se excluye explícitamente y se devuelve excluded_nonvehicle_tracks. Clases no catalogadas se conservan con requires_review y advertencia de alcance, incluidas en el total automatizado sin asegurar su categoría física. Orden de respuesta estable por class_key; no fusionar sedan/suv/car. Suma de classes.track_count==total_tracks. Es conteo de identidades locales, no garantía de vehículos físicos únicos tras pérdida/reasignación del tracker.

GET no inicia backfill ni OCR. Trabajos nuevos actualizan inventario con publish atómico; antiguos son examinados por inicialización/worker y declaran su capacidad. Un final válido no cambia por rewind, línea, selección de ficha ni OCR.

## Exportación etiquetada y compatibilidad de versión

GET/POST sobre /export sin renderer conservan VideoExportStatus/archivo legacy. La query opt-in solo admite renderer=vehicle-labels-v1, una vez. POST no admite cuerpo y exige análisis complete; crea/reutiliza variante sin inferencia. GET lee esa variante: waiting si nunca se solicitó; cola/rendering/encoding/ready/failed como hoy, pero cacheados por job+renderer. Un legacy ready no satisface esta variante.

URL solo en ready: /api/v1/video-jobs/{job}/playback/export/content?renderer=vehicle-labels-v1. HEAD/GET validan propietario, TTL, versión, disponibilidad y Range; nunca generan trabajo. El gateway permite esta descarga nativa con la sesión vigente y las protecciones de medio existentes; las operaciones JSON mantienen CSRF/sesión. Ruta antigua annotated-video no cambia de archivo silenciosamente. Worker/orquestación, prioridad de análisis y perfiles separados se reutilizan, sin doble modelo.

Cada caja usa clase observada del cuadro y Track ID, display_bbox cuando exista y la paleta compartida. Renderer incluye todas las etiquetas, acentos y líderes de asociación; no incluye texto de placa ni un contador nuevo en la descarga. Dimensiones, duración y velocidad siguen el exportador vigente; los casos VFR deben comprobar su semántica existente, no prometer conservación de audio/PTS que este cambio no implementa.

## Errores y límites

- 404 artifact_not_found para padre ajeno/desconocido, inspection_not_found/media_not_ready para derivados locales; no confirmar existencia ajena.
- 409 generation_stale, frame_not_ready, track_not_in_frame, count_revision_stale, interval_not_ready, plate_not_ready o analysis_not_ready, según operación.
- 410 artifact_expired si el padre propio vence/se retira; contexto con TTL menor410 inspection_expired es local y no retira la reproducción del padre todavía vigente.
- 422 query_invalid/body_invalid/invalid_line/renderer_invalid; no aceptar unknown/duplicate parameters ni números no finitos. Los errores siguen Error vigente con code/message/request_id, sin rutas ni excepciones internas.
- 429 inspection_queue_full/inspection_limit/inspection_bytes_limit con Retry-After para saturación temporal; alcanzar el máximo retenido por job se explica como cuota hasta TTL, no prometer que reintentar creará capacidad.
- Limitar extracción a300 cuadros/5s incluyendo arranque de un subproceso PyAV-only: watchdog en padre con terminate/join, lease mantenido y temporales privados retirados antes de liberar; sin modelos ni shell/ventana en el hijo. Verificar PTS/bbox/bytes y vigencia antes de publicar; el contexto termina unavailable con inspection_frame_unavailable/inspection_decode_limit; un fallo no se convierte en crop de otro momento. Workers validan padre también antes/después de modelos.
- 503 para exportación saturada/servicio no listo según política vigente. Un fallo del renderer no falla el análisis ni cambia el resumen.

## Comprobaciones semánticas adicionales a JSON Schema

Puntos distintos; bbox dentro de dimensiones y min<max; source PTS/rationales correspondientes al frame index; end>start; identidad presente en el cuadro; hijos/URLs pertenecen al job/contexto; TTL no amplía padre; ready/pending/unavailable coherentes con nullabilidad; sumas/clases; final implica cobertura completa; contextos/generaciones/revisiones no se mezclan. Los ejemplos son sintéticos, no proceden de vehículos ni videos del usuario.

Si las dimensiones del video impiden físicamente alojar una etiqueta legible aun usando las ubicaciones permitidas, la exportación termina failed con export_label_layout_unrepresentable; no se publica ready sin identidades, se modifica resolución ni se oculta una etiqueta. El diseño minimiza solapamientos de escenas densas; no promete separación perfecta en todo contenido arbitrario. La validación visual principal usa las fuentes admitidas habituales del proyecto.
