# Data Model: Iteración 010

Modelo previsto, no migración ejecutada. Se conserva SQLite/lock/transacción de ProgressiveStore; tablas nuevas usan job/generation como pertenencia, y las filas p_video/p_frames siguen siendo la fuente de autoridad. No modificar IDs del tracker ni modelos/pesos.

## 1. InspectionContext / p_video_inspections

| Campo | Regla |
|---|---|
| inspection_id | UUID opaco, clave primaria |
| job, generation, owner | Padre autorizado; owner no se devuelve |
| track_id, frame_index, policy_version | Positivos/índice>=0, única clave `(job,generation,track_id,frame_index,policy_version)` |
| source_pts, time_base_num/den, start_us/end_us | Se resuelven del recibo/timeline servidor, no del cliente; PTS racional exacto |
| raw_bbox, class_name, observation_kind, confidence/confidence_kind | Geometría validada del recibo; measured/predicted explícito. Confianza persistida, measured para medición o last_measured para caja predicha; nunca una confianza nueva inventada |
| state | queued, preparing, processing, ready, partial, unavailable, failed, not_applicable |
| result_revision | Monótono, cambia datos de esa inspección sin cambiar evidencia |
| vehicle_asset_id, plate_asset_id, paths | IDs y rutas privadas inmutables una vez publicados; cada plate deriva del crop de esa inspección |
| attributes, plate, error_code | Resultados independientes y seguros con provenance ligada al inspection_id |
| expires_at, bytes_reserved/actual, claimed | TTL<=min(padre,TTL enriquecimiento), contabilidad de cuotas, propiedad del worker |

Relaciones: un padre posee muchas inspecciones; una inspección consulta un solo frame/track. No insertar sus assets en el ranking legacy p_evidence. Un resultado negativo sobre frame A no satisface la clave de frame B.

Estados: queued→preparing→processing→ready|partial|failed|not_applicable; preparing→unavailable cuando no hay correspondencia/recorte. Vehicle asset puede publicarse al pasar a processing y nunca cambiar después; plate asset se publica una vez al localizarse. Resultado parcial conserva datos válidos y errores de otros componentes. Sin modelos se conserva el recorte disponible y se informa capacidad no aplicable.

Publicación: reclamar con transacción breve, lease de fuente y extracción fuera de lock. El padre lanza una extracción PyAV-only en un subproceso efímero sin app.main/modelos, con argumentos estructurados y sin shell/ventana; conserva el lease. Watchdog de5s desde el arranque, límite300 cuadros y8MiB de salida; timeout/retirada implica terminate/join y limpieza. Validar el PTS racional exacto y geometría del resultado al salir el hijo, validar padre/generación/TTL y publicar por rename antes de referenciarlo. Nunca exponer un archivo a medio escribir. Processing interrumpido termina failed/inspection_interrupted, no se repite OCR automáticamente. Un preparing recuperable puede reencolarse sin duplicar crop; valida presencia/hash de cualquier archivo ya congelado. Retirada/TTL elimina metadata sensible y archivos con lease al liberar lectores. Si vence primero el TTL de inspección, conservar hasta el vencimiento padre un tombstone mínimo con clave canónica, ID y expires_at originales; no media, atributos, placas ni bbox. Repetir POST de esa clave devuelve410 inspection_expired y no renueva retención ni crea trabajo. Tombstones cuentan para las128 admisiones por job; liberar cuota de bytes tras eliminar assets sin liberar admisiones. Al vencer/retirar padre se retiran también estos recibos.

## 2. InspectionAsset

IDs opacos y tipo vehicle|plate. Original PNG inmutable; blob de navegador se cachea por inspection_id/asset_id hasta cambio de contexto/TTL, siempre en memoria. El zoom y estado original/procesada se asocian al contexto, sin reiniciarse por result_revision. Una vista procesada de placa es derivado visual determinista del mismo original, nunca reemplaza evidencia OCR ni texto reconocido.

Reutilizar política/transformación de plate-preview existente separando su acceso de imagen del de video. Añadir `plate-preview?profile=...` privado de inspección con perfiles admitidos y metadatos específicos de inspección cuando la placa exista. `InspectionPlatePreviewMetadata` conserva inspection_id/plate_asset_id, job/generation/track/frame/time, `coordinate_space=plate-crop`, dimensiones original/procesada, transformación afín source_to_processed de6 números finitos, perfil/política/TTL y `display_only=true`. No inventar source_id/enrichment_job_id/detection_id de imágenes ni usar su parser; compartir solo transformación/presentación. GET puede producir una transformación visual acotada del crop congelado según política existente, pero no decodifica fuente ni ejecuta OCR; diferenciar esta transformación de GET de estado sin efectos. La disponibilidad se declara y sus archivos derivados cuentan para cuota/TTL. Perfil desconocido se rechaza; no crear una nueva lectura.

## 3. DirectedCountConfiguration / p_directed_count_state

Una fila por job con generation y revision monótona, incluso disabled; puntos normalizados finitos0..1 distintos, direction `negative_to_positive|positive_to_negative`, policy `finite-center-v1`, status disabled|building|ready|unavailable, cursor de frames y coverage_until_us. `expected_revision=0` solo permite primera creación; aplicar cambios exige revisión actual. Aplicar idéntica configuración vigente es no-op. Conflicto→409 y nuevo GET; no mezclar borrador y configuración activa.

DELETE aumenta revisión y deja tombstone sin geometría/medios, dentro del TTL del padre. Las filas derivadas de revisiones antiguas se eliminan de forma acotada. Ningún cambio afecta p_count_state/p_count_events legacy, resumen ni detecciones.

## 4. DirectedTrackState / p_directed_count_tracks

Clave `(job,revision,track_id)`. Guarda último centro medido/PTS/índice, último lado no nulo, contacto con segmento pendiente y si ya existe evento. Solo cuadros detection_performed=true o procedencia histórica verificada actualizan el estado. Coordenadas fuente corregidas por orientación; las coordenadas normalizadas del editor se convierten según dimensiones fuente.

Distancia cero numérica=1e-6 píxeles. Mantener contacto finito a través de muestras sobre línea; confirmar solo al cambiar entre lados estrictos. Tocar y volver al mismo lado descarta contacto. Movimiento inverso/exterior actualiza referencia pero no consume un futuro primer cruce válido. No hay inferencia de cruce antes de la primera medición.

## 5. DirectedCrossingEvent / p_directed_count_events

Clave única `(job,revision,track_id)`, direction elegida, confirming_frame_index y time_us=start_us de la medición confirmatoria. Índice `(job,revision,time_us)` para conteo histórico. El número mostrado es cardinalidad de eventos con time_us<=posición, nunca Track ID máximo. Varios eventos en el mismo cuadro suman varias unidades.

Reducer: worker procesa recibos en orden ascendente, hasta200 por transacción, con cursor y eventos en un único commit. Publicación repetida/reinicio no duplica. Al cambiar revisión, resultados anteriores dejan de ser consultables como actuales. GET devuelve total solo si at_us<covered_until_us y at_us<available_until_us; el extremo es exclusivo y la igualdad podría corresponder a un evento del siguiente cuadro no reducido. Con prefijo vacío solo at_us=0 devuelve pending/null o disabled/0; mientras construye, total=null y status pending con cobertura. Si el reducer alcanza todo el prefijo, status ready aunque el análisis continúe; nuevos lotes vuelven a dejar cola pendiente.

## 6. DetectionClassVote / p_detection_class_votes

Clave `(job,generation,track_id,class_key)`; observation_count>=1 y max_confidence finita0..1. class_key=nombre strip/lower; vacío→`unknown`. No fusionar subtipos. Votar solo una vez por identidad/observación medida recién insertada. Ganador: votos descendentes, confianza máxima descendente, class_key ascendente. Empate no depende del orden del lote.

## 7. DetectedIdentity / p_detection_identities

Clave `(job,generation,track_id)`, canonical_class, first_seen_us/last_seen_us, measured_observations. Canonical class puede cambiar mientras llegan votos; al cerrar cobertura final queda congelada. Las predicciones, selecciones de ficha y líneas no crean identidades ni votos. No usar p_tracks ni top-K de enriquecimiento.

Taxonomía `vehicle-inventory-v1`: car/truck/bus/van/pickup/suv/sedan/hatchback/mpv/estate/bicycle/motorcycle son vehículos conocidos; person se declara no vehicular y se excluye del total. Ganadores desconocidos se muestran explícitamente con requires_review, conservan clave de origen y forman parte del total automatizado con advertencia «clases no catalogadas»; no se descartan silenciosamente. No reutilizar VEHICLE_CLASSES, que define elegibilidad de enriquecimiento.

## 8. DetectionSummaryState / p_detection_summary_state

job/generation/policy_version, cursor, covered_until_us, covered_revision y status building|partial|final|unavailable. Un estado building puede dar cero confirmado sin llamarlo resumen final. Completo solo si análisis complete y cursor==frames publicados con procedencia suficiente; parcial si trabajo falla/cancela con datos válidos. GET devuelve total_tracks, clases con track_count, excluded_nonvehicle_tracks y requires_review; sum(classes.track_count)==total_tracks. El resultado no depende del playhead.

Reducción nueva: en publish, agrupar votos del lote y actualizar identidades/cursor dentro de la misma transacción que los frames nuevos, sin BEGIN anidado. Saltar recibos idénticos repetidos. Backfill antiguo: lotes200, cursor durable, captura de prefijo y catch-up antes de final. Si faltan marcas, verificar contra video_detections medida; sin procedencia no declararlo completo. No disparar backfill desde GET.

## 9. LabelExportVariant / p_video_export_variants

Clave `(job,renderer_version)` con `vehicle-labels-v1`; state waiting|queued|rendering|encoding|ready|failed, processed_frames, error_code, rutas privada final/temporal y TTL padre. El worker existente alterna solicitudes legacy/variantes; no duplicar hilos/modelos ni generar al leer. No reutilizar p_video_exports ready como variante etiquetada. Repetir solicitud durante cola/ready devuelve la misma variante; failed permite reintento explícito según política de exportación vigente. Nueva versión debe producir ruta/ETag distintos.

Estados y validación de H.264/Range/retiro conservan la exportación actual. Un renderer usa display_bbox cuando existe y la clase de la observación de ese cuadro, no canonical_class final. Memoria de colocaciones solo para identidades activas del render; no guardar posiciones por todos los cuadros.

## 10. Migración, capacidades y limpieza

- Crear tablas/índices mediante inicialización idempotente, sin ALTER destructivo ni modificar filas de tracking/legacy. Versiones/policies distinguen datos verificables de reconstrucciones.
- Capacidades independientes: inspección temporal según fuente+PTS, conteo dirigido según mediciones/geometría, resumen según procedencia/inventario; error de una no retira capacidades válidas de las otras.
- Fuente VFR, PTS no cero y rotación deben usar la misma timeline que reproductor/exportador. Para cuadros antiguos sin frame time_base explícita, usar base de stream persistida y comprobar correspondencia; si no es demostrable, unavailable. Nuevos recibos privados pueden persistir base temporal del frame para equivalencia racional sin cambiar FrameSlice público.
- Agregar todas las tablas nuevas y directorios temporales/variantes a cleanup/withdrawal de ProgressiveStore y al janitor. Parent check antes de reclamar, inferir y publicar. No ampliar TTL por reabrir, polling, exportar ni backfill.
- Controles de cuota reservan por transacción antes de crear; un mismo contexto reutilizado no consume otra entrada. Fallos liberan temporales/reservas sobrantes; filas terminales sensibles se conservan solo hasta su TTL y después únicamente el tombstone mínimo hasta TTL padre, contando para el límite de admisiones.
- Logs registran fases, IDs opacos, revisión, latencia/bytes/cobertura y códigos seguros; nunca texto OCR, placas, archivos originales, crops, rutas ni secretos. Perfiles de inspección/exportación se separan de video-profiles para que --latest siga siendo análisis.

## Configuración nueva prevista

| Variable backend | Inicial | Regla |
|---|---:|---|
| VIDEO_INSPECTION_MAX_QUEUED | 20 | Entero positivo, cola global |
| VIDEO_INSPECTION_MAX_CONTEXTS_PER_JOB | 128 | Admisiones incluyendo recibos vencidos hasta TTL padre |
| VIDEO_INSPECTION_MAX_BYTES_PER_JOB | 134217728 | Bytes derivados retenidos/reservados por job |
| VIDEO_INSPECTION_MAX_RESOURCE_BYTES | 8388608 | Máximo de un asset/derivado |
| VIDEO_INSPECTION_DECODE_MAX_FRAMES | 300 | Máximo de cuadros tras seek |
| VIDEO_INSPECTION_DECODE_TIMEOUT_SECONDS | 5 | Plazo del subproceso incluido arranque; positivo |

No modificar variables de detección, pesos, confianza, hilos, intervalos o autenticación. La implementación debe añadir ejemplos sin secretos y validar recurso<=cuota de job. Estos valores se fijan como límites operativos iniciales, no como rendimiento garantizado.
