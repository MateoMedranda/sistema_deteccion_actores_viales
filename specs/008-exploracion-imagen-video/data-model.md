# Data model: Exploración de imágenes y video

**Estado**: diseño para008; no migraciones ejecutadas. [Spec](spec.md), [gateway](contracts/gateway.md), [backend](contracts/backend-additions.md) y [UI](contracts/frontend-interactions.md).

## 1. WebConfiguration — solo servidor

| Campo/variable | Regla |
|---|---|
| WEB_BACKEND_URL | Origen http(s) fijo, sin usuario/clave/query/fragmento/path distinto de /; HTTPS salvo loopback. No procede del navegador. |
| WEB_BACKEND_API_KEY | SecretStr no vacío, no placeholder; una credencial/principal por instancia. No serializar Settings. |
| WEB_ORIGIN | Origen público exacto sin wildcard; http solo loopback, https para remoto. Host debe corresponder. |
| WEB_STATIC_DIR | frontend/dist por defecto; no exponer otros directorios, .env o archivos fuente. |
| WEB_SESSION_TTL_SECONDS |900 predeterminado; permitido60..3600; absoluto, no renovado por solicitudes. |
| WEB_MAX_SESSIONS |128 predeterminado;1..1024. Capacidad agotada429, no expulsar una sesión activa para admitir otra. |

.env.web privado; .env.web.example futuro contiene placeholders. Reiniciar gateway rota secreto efímero, invalida sesiones y no cambia autenticación de backend. Un despliegue remoto requiere ingreso privado/autenticado existente; no se infiere confianza de un header enviado por el visitante.

## 2. WebSession — RAM sin medios

Campos internos: hash de session_id aleatorio256bits, csrf_token aleatorio256bits, epoch UUID, created_at/expires_at UTC, revisión de credencial configurada y hasta2 intenciones activas/corrientes. Un principal configurado por gateway, sin selección pública de propietario. La cookie contiene solo el identificador opaco.

Estado: absent -> ready -> expired/reset/rejected. No hay refresh deslizante. Reset reemplaza epoch y retira ambos workspaces. Cleanup elimina sesiones vencidas en<=2s; cierre borra RAM. Estado público y capacidades en schemas.json/WebSession; nunca clave, URL upstream ni ID del propietario.

## 3. WorkspaceState — solo memoria del navegador

Global: sessionEpoch, sessionExpiresAt, connectionStatus, activeMode(image|video). Inicial image. Dos paneles montados; hidden no borra estados ni detiene TTL. Al ocultar Video, pausar reproducción y conservar currentTime. Cambio de epoch desmonta/limpia ambos.

Por espacio: generation monotónica, fuente vigente, controladores abort, fechas límite y timers. Una imagen y un video por sesión, sin historial ni localStorage de medios/resultados/secretos. Refresco completo inicia otra sesión de UI y no reenvía POST automáticamente.

Identidades:
- imagen: epoch+generation+sourceId+enrichmentJobId+detectionId.
- video: epoch+generation+videoJobId+enrichmentJobId+trackId.
- conteo: epoch+generation+videoJobId+lineVersion+countJobId.

Toda respuesta, página, evento/timer y medio se verifica contra la identidad vigente antes de publicarlo.

## 4. SceneViewport

Campos: sourceId/generation, naturalWidth/Height, mode(fit|intrinsic), scale finita>0 y<=4, scrollLeft/Top, anchor normalizado[0,1]², pointerId/dragOrigin/suppressActivation transitorios.

Ajustar=min(1,anchoInterior/W,altoInterior/H); contenedor max-height=min(70vh,720px), min-width:0 y scroll propio.100%=1px original por px CSS. Imagen y contornos viven en un escenario W*scale×H*scale; cajas porcentuales de geometría canónica, border-box/trazo CSS constante. Resize conserva ancla; dimensiones0 de un panel hidden no sobrescriben el encuadre.

Reset/fuente nueva -> fit/scroll inicial. Zoom no modifica selección/crops/datos ni TTL. Arrastre>=6px CSS invalida únicamente la activación de ese gesto; pointercancel/blur limpian el estado transitorio.

## 5. ClassPresentation

app/domain/class_presentation.json será fuente única: version1, classes con13 claves y {label,color}; fallback_color=#64748B. Los valores/copias de007 se conservan byte-semánticamente. Clave=class_name.trim().toLowerCase(); desconocida conserva nombre como texto escapado. No contiene elegibilidad ni identidad. Paquete Python incluye el JSON; frontend importa el mismo activo. Pruebas de paridad contra el contrato007.

## 6. RawObservation y PresentedBox

RawObservation reutiliza FrameDetection sin cambios: job_id, frame_index0-based, track_id>=1, class_id/name, confidence y bbox half-open entera en el cuadro canónico. Persiste para conteo y selección de evidencia.

PresentedBox es efímera: frame_index/track_id/class, bbox filtrada entera/clamp y profile_id=gated-ema-v1. Nunca se guarda como detección/evidencia ni se serializa sustituyendo raw.

Estado del filtro por(job,track,class): último frame_index, última caja raw y última caja presentada. Retiene únicamente identidades presentes en el cuadro actual, más miniatura gris32×18 del cuadro anterior. Reinicio por:
- primer cuadro, hueco, cambio de clase o corte MAD normalizada>=.25;
- IoU raw consecutiva<.25;
- desplazamiento del centro>.25*diagonal de la caja actual;
- razón de ancho o alto fuera de[2/3,1.5].

Antes de filtrar, la representación recorta la caja raw a los límites del cuadro, igual que el dibujo anterior; no modifica la observación persistida. Una caja visible degenerada no se dibuja y se registra como inválida para la validación, no se excluye favorablemente. La caja autorizada para comparar IoU es esa región visible.

Candidato: combinación EMA de(cx,cy,w,h) con alphas[.65,.8,.9,1], en ese orden. Para cada alpha convertir a enteros por round half-to-even, clamp a[0,W]×[0,H], rechazar degenerada y comprobar IoU>=.90 respecto raw actual. El último caso es la caja visible raw exacta, sin redondearla de nuevo. Estado siguiente=salida elegida. Sin observación actual no hay caja ni extrapolación. Ningún lock de store envuelve esta transformación.

## 7. VideoJob — adiciones compatibles

Se conserva status=queued|processing|completed|failed|cancelled y todas las rutas/campos existentes. Añadir, nullable para registros históricos:

| Campo público | Semántica |
|---|---|
| processing_phase | queued|frames|encoding|publishing|ready|failed|cancelled, o null si histórica/desconocida. |
| frame_total_confirmed | bool; true solo después de EOF real. |
| video_metadata | null hasta ready; objeto de salida confirmada descrito abajo. |
| eligible_track_count | null antes de ready, luego número de track IDs elegibles distintos según configuración del servidor. |
| classes_present | null antes de ready, luego lista única de nombres observados, sin confundir observaciones con vehículos. |

processing_phase=frames/encoding/publishing exige status=processing. ready exige completed, metadatos confirmados y conteo/clases presentes. Fases terminales coherentes con status. Migración de registros antiguos conserva null; no fabricar metadatos desde un total antiguo forzado.

video_metadata={width,height,fps,frame_count,duration_seconds,timebase:"processed-cfr"}. frame_count es número real de cuadros escritos; duration=frame_count/fps. Son propiedades del MP4 generado, no PTS exactos del original. Históricos sin confirmación no reciben timestamps inferidos.

Durante lectura processed_frames cuenta cuadros reales, total_frames es estimación inicial y frame_total_confirmed=false. EOF actualiza total_frames al conteo real y frame_total_confirmed=true. progress_percent histórico continúa0..100 de cuadros, saturado; puede ser100 mientras encoding. La UI nueva NO lo interpreta como finalización de la etapa: en encoding/publishing muestra progreso indeterminado.

Publicación: transacción bajo lock comprueba propietario/estado processing/TTL antes de asociar MP4 y raw observaciones; devuelve desenlace efectivo. Cancelación/expiry/fallo no publican ni guardan detecciones tardías. Las rutas siguen404/410 según autorización conocida. El worker conserva cupo hasta detener hilo/FFmpeg y limpiar parciales.

## 8. IdempotentIntent — asociado a fila existente

Header opcional Idempotency-Key,16..128 caracteres [A-Za-z0-9_-]. SHA256 del valor en columna nullable idempotency_key_hash. UNIQUE parcial(owner_key_id,idempotency_key_hash) por store. request_fingerprint SHA256:
- video: MIME normalizado + separador nulo + bytes originales bajo validación/cotas; no nombre/path.
- enriquecimiento: JSON canónico de source.kind/source_id.

Admisión y replay bajo mismo lock/transacción: mismo propietario/clave/fingerprint devuelve recibo original; distinto fingerprint409 idempotency_conflict. No renovar created_at/expires_at. No duplicar cola ni cómputo. Legacy sin header tiene null y mantiene comportamiento.

La garantía dura el TTL original de la fila; no hay deduplicación eterna. Limpieza elimina columnas junto con el job. Upload duplicado/conflictivo elimina su staged adicional sin tocar el original. Migración PRAGMA idempotente y INSERT con nombres explícitos, no VALUES posicionales.

Gateway deriva clave upstream con HMAC de secreto efímero+sesión+operación+intención UUID del cliente; no revela ese secreto. Un resultado incierto conserva intención; retry explícito tras fallo conocido crea otra y descarta la referencia anterior. No reenviar una intención fuera de sesión/TTL. Solo una tentativa activa por fase/fuente en la UI.

## 9. VideoAnalysisState

Máquinas separadas:
- procesamiento: idle/uploading/checking/queued/processing/ready/failed/cancelled/interrupted/expired.
- medio: idle/loading/available/failed/expired.
- enriquecimiento: waiting/submitting/queued/processing/completed/not_applicable/failed/cancelled/interrupted/expired.
- resultados: idle/loading/ready/failed; página actual25 y ficha seleccionada.
- conteo: máquina003 existente ligada a fuente/línea.

Autoencadenado solo desde video completed+ready vigente, eligible_track_count>0 y no intención previa en curso. Si0 ->not_applicable;400 no_eligible_vehicles también se interpreta así ante una carrera.503 de capacidades no borra video. Cancelar enriquecimiento no cancela video ya terminado.

Sondeo sin superposición cada1.2s. Error de red ->interrupted, no failed de negocio; Reanudar hace GET. Si falta recibo de POST, recuperación explícita reenvía MISMA intención y payload, no otra tentativa.401 global de credencial/sesión retira ambos espacios;404/410 de fuente retira su grupo de medios/resultados; error de tratamiento conserva las otras evidencias vigentes.

## 10. VideoTrackDetails y EvidenceReference

Lista/ficha usa identidad completa, track_id real y clase del servidor. detection_id sigue siendo referencia de unidad del resultado, no identidad de trayectoria. Sin crops de video nuevos; no llamar a rutas007 exclusivas de imagen.

Conservar evidence_frame_indexes del resultado/placa y evidence_frame_index por atributo: enteros únicos no negativos y, con frame_count confirmado, menores que ese conteo. Ausencia histórica=desconocida; nunca derivar un origen OCR desde used_enhancement o vista activa.

Referencia visible: cuadro i y, cuando hay metadata confirmada, i/fps del video procesado, distinta de currentTime. Si varios cuadros respaldan una lectura, se muestran como evidencia disponible; no inventar cuál originó el texto. No transformar selección/búsqueda en inferencia.

## 11. Retención y recursos

TTL aplicable=min(sesión,fuente,job cuando corresponda), sin deslizamiento. Backend conserva límites actuales de workers/colas/medios; UI no cambia configuración. Gateway cierra streams al deadline/desconexión, no almacena cuerpos/medios. Página anterior y ficha anterior se reemplazan; hidden no suspende limpieza. Más detalles en contratos/protocolo.
