# Data model — 009 Video progresivo

Diseño aditivo; las entidades legacy no cambian de significado. Contratos públicos en [contracts/](contracts/README.md).

## Cronología y geometría

- Cada frame del decoder contiene frame_index desde0, pts entero con signo, time_base racional positiva, BGR24, width/height, rotación/corrección de orientación y duración cuando exista.
- Persistir PTS exacto como entero de64bits; exponerlo como texto si es necesario evitar pérdida de precisión de JSON. start_us/end_us son enteros no negativos <=2^53-1 en la cronología reproducible normalizada de la fuente, no frame_index/fps.
- Validar el mapeo contra el origen del stream/edit list y los tiempos del video en navegador. No restar ciegamente el primer PTS si la fuente expone otra cronología.
- Intervalo [start_us,end_us), end>start, siguiente inicio igual al final anterior. Confirmar con un frame de lookahead; el último usa duración validada y termina en duración confirmada de fuente. Tiempos inconsistentes producen timeline_unrepresentable, no una cronología inventada.
- La geometría se expresa en píxeles de la imagen canónica decodificada. metadata registra la transformación de orientación que relaciona source pixels y canvas. Cajas raw son salida del detector; display_bbox conserva PresentationFilter calculado durante inferencia, nunca recalculado por seek.
- No se cambian detección, tracker ni muestreo. Se requieren pruebas de píxeles, cajas y orientación contra el baseline.

## Entidades persistentes

| Entidad / clave | Campos principales | Reglas |
|---|---|---|
| VideoProgressive / job_id | owner_key_id privado, generation UUID, revision, analysis_state, export_state, frames_processed, frames_published, available_until_us, last_frame_start_us, duration_us, source_closed, expires_at, reason_code | generación inmutable, un recurso por trabajo progresivo; TTL heredado del trabajo |
| PublishedBatch / job_id,generation,sequence | first/last_frame, start_us,end_us, revision, committed_at | secuencia y cobertura contiguas; cuadros inmutables; ninguna publicación tras revocación/expiry |
| FrameInterval / job_id,generation,frame_index | pts,time_base_num/den,start_us,end_us,width,height,published_revision | incluir vacíos; duración positiva, cobertura continua |
| Observation / frame_index,ordinal | track_id,class_id,class_name,confidence,raw_bbox,display_bbox nullable | ordinal estable dentro del cuadro; confidence0..1, bbox finita dentro de geometría; display nullable si filtro oculta una observación |
| TrackUnit / unit_id UUID | job_id,generation,track_id,discovery_ordinal,class_name,first/last_seen_us,state,final,result_revision,evidence_revision | unique(job_id,generation,track_id); nunca usar detection_id final como identidad progresiva |
| TrackEvidence / evidence_id UUID | unit_id,frame_index,time_us,raw_vehicle_bbox,confidence,rank,provisional,private_digest,vehicle_artifact,plate_artifact,expires_at | datos originales antes de dibujar; top-K + provisional evaluada; no rutas privadas en respuesta |
| TrackEvaluation / unit_id,evidence_id,policy_digest | estado, atributos, placa, procedencia, error seguro,attempt_count,result_revision | evaluación única por evidencia/política; lectura no ejecuta inferencia; retry de transporte reutiliza resultado |
| ProgressiveEnrichment / job_id,generation | revision,source_closed,discovered_units,provisional_ready_units,terminal_units,status | total abierto mientras source_closed=false; 100% solo con fuente cerrada y unidades finales terminales |
| ResourceReceipt / artifact_id | job_id,owner,digest,kind,relative_storage_key,expires_at,publication_revision,in_use | recibo durable y cleanup por propiedad; no extensión del TTL por lectura/publicación |

Las tablas nuevas viven en la base de video. Incluir índices por (job,generation,start_us), publicación, track y cola pendiente. Migración aditiva/idempotente y lectura de filas legacy sin generación; no reinicializar bases ni exigir pesos para migrar.

## Publicación y consistencia

1. Producir un lote de cuadros y anotar su cobertura completa, incluidos vacíos. Extraer evidencia sobre original antes de pintar.
2. Escribir/cerrar archivos temporales con nombres opacos y recibos. Fuera de la transacción, nunca inferir ni transmitir un archivo mientras se escribe.
3. En una transacción de escritura breve: comprobar propietario/generación, source abierto, no cancelación y now<expires_at; insertar cuadros/observaciones/evidencias; avanzar secuencia y revision solo si continúa el último final confirmado.
4. Commit hace visibles lote y límite simultáneamente. Un duplicado exacto devuelve el estado existente; un duplicado conflictivo o hueco se rechaza. No tomar max(timestamp).
5. Tras commit, el scheduler puede consumir referencias de evidencia confirmada. Un crash previo deja huérfanos para purga; uno posterior conserva el lote.
6. El watermark autoritativo solo crece dentro de la generación viva. Revocar/expirar retira el recurso completo y manda limpiar el cliente; no se transforma en un watermark menor reutilizable.
7. Archivos publicados son inmutables. El control de propiedad y TTL se repite al leer y durante streams; referencias en uso retrasan borrado físico, nunca acceso lógico.

## Estados

### Análisis y salida final

analysis_state: queued → analyzing → complete | partial_failed. Sin primer lote un fallo sigue partial_failed con available_until_us=0, sin reproducción válida. El estado HTTP de recurso retirado es410 para su propietario conocido, no una fila pública reutilizable.

export_state: waiting → encoding → ready | failed. Legacy VideoJobStatus mantiene queued/processing/completed/failed/cancelled; completed exige su salida anotada de siempre. analysis_state=complete puede coexistir con export_state=failed y legacy failed.

Fallo técnico/timeouts cierran descubrimiento, detienen publicación y conservan el prefijo y fuente necesarios hasta expires_at. Reinicio de un trabajo progresivo en vuelo marca partial_failed/processing_interrupted sin borrar/reencolar cuadros ni recrear IDs; trabajos legacy conservan su recovery anterior.

Cancelación explícita, DELETE playback y sustitución de fuente revocan el recurso, cancelan colas y bloquean commits tardíos. Cancelación no equivale a fallo técnico. Cierre normal del servidor no borra indiscriminadamente recursos confirmados; se purgan scratch e inputs sin necesidad vigente, y quedan solo medios necesarios para resultados autorizados.

### Enriquecimiento

Unidad: waiting_evidence → queued → processing → ready | partial | failed | not_applicable; final=false mientras la fuente siga abierta. Un resultado provisional puede actualizarse a una revisión nueva, nunca a una anterior. Al cerrar fuente se calcula top-K definitivo y termina cada unidad (final=true), incluida cualquier fallida/cancelada por interrupción.

Agregado público: discovering mientras source abierto; processing cuando cierra y quedan tareas por drenar; complete, partial o failed cuando todas son terminales. Si no hubo elegibles: not_applicable. No se comunica porcentaje final con denominador todavía creciente. En timeout se drena lo confirmado dentro del plazo o se marca cada pendiente failed con motivo seguro; nunca pendiente indefinido. Revocación cancela todo y retira acceso.

Una evidencia temprana provisional + K candidatas globales por (-confidence,frame_index). Si la provisional integra top-K, se reutiliza; si no, no influye en consenso final. Máximo K+1 evaluaciones únicas; candidatos no consumidos desplazados se eliminan con seguridad. Reutilizar el consenso actual, umbrales y modelos, sin suavizar lecturas para parecer estables.

## Lecturas y cache

El estado público PlaybackState publica revision de cuadros y enrichment.revision separadas. Solicitudes de cuadros se atan a job/generation/snapshot y ventana temporal; cursor opaco vincula esos valores y continuación. Los cuadros son inmutables, permitiendo snapshots históricos mientras el trabajo siga vigente.

Paginación por presupuesto de bytes y observaciones. Un frame muy denso puede dividirse usando observation_offset/observation_total; el cliente reúne todas las partes antes de admitirlo. Vacío: total0, offset0 y lista vacía, no omitirlo. Una ventana no se declara completa hasta agotar su cursor y validar cobertura. No cortar cajas para cumplir el tamaño.

El límite visible efectivo es el mínimo del watermark autoritativo, cobertura local continua disponible desde la posición objetivo y disponibilidad del medio. Un salto al extremo exclusivo usa last_frame_start_us del último cuadro completo. Caché LRU de16MiB/30s acumulados; se vuelve a consultar historia expulsada, sin inferencia. Selección conserva una sola ficha con su revisión; cualquier trabajo/generación nueva cancela fetch y elimina cache anterior.
