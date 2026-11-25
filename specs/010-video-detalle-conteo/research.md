# Research: Iteración 010

Fecha: 2026-11-24. Estado: decisiones de diseño resueltas, implementación pendiente. Investigación mediante tres agentes de solo lectura y verificación del coordinador en el checkout principal; sin ejecutar modelos, pruebas de producto ni comparación larga.

## R1. Ficha común y scroll

- **Evidencia**: `frontend/src/styles.css` fija `.progressive-details` con `max-height:min(850px,calc(100vh - 120px));overflow:auto`. `ProgressiveTrackResults.tsx` ya combina `vehicle-details progressive-details`, pero sus reglas alteran medidas de la ficha de imágenes.
- **Decision**: Compartir shell, tipografía/espaciado y presentación de recortes/placa con adaptadores de datos distintos. Quitar altura/scroll de la ficha completa, conservar controles de zoom locales y desplazamiento normal de página.
- **Rationale**: Corrige la causa concreta sin rediseñar el flujo de imágenes ni perder el contexto temporal del video.
- **Alternatives considered**: Otro panel independiente duplicaría estilos; eliminar todos los overflow rompería la inspección ampliada de placa.

## R2. Consulta ligada al fotograma

- **Evidencia**: `ProgressiveVideoPlayer.tsx` selecciona solo track_id; el efecto POST `/tracks/{id}/enrich` no depende del cuadro. `ProgressiveEvidence.request()` deduplica `(job,track)` y congela top-K por confianza, con desempate hacia índices antiguos. `ProgressiveTrackResults` toma `evidence[0]`; `ProgressiveEnrichment.refresh()` reconstruye la lista al completarse resultados. Este es un camino verificable hacia recortes antiguos/cambiantes, no una afirmación de que todo polling parpadee.
- **Decision**: Contexto aparte con clave `(job,generation,track,frame_index,inspection_policy_version)`, evidencia inmutable y resultado progresivo. La selección captura el cuadro realmente pintado, no `currentTime*fps`; la respuesta se filtra por contexto y token de selección.
- **Rationale**: Un resultado negativo temprano deja de bloquear consultar al mismo vehículo más cerca. El primer recorte y el de placa pertenecen al mismo contexto y no compiten con los candidatos legacy.
- **Alternatives considered**: Añadir tiempo a la selección sin cambiar la caché por track conserva el error; elegir el «mejor» recorte automático no cumple el instante seleccionado; enriquecer toda la trayectoria reintroduce coste no solicitado.

## R3. Extracción exacta, procedencia y límites

- **Evidencia**: `TimedVideoDecoder` conserva PTS/start/end y conversión ITU601/BICUBIC/rotación aprobada; no ofrece acceso aleatorio. `p_frames.payload` guarda pts, start_us/end_us y detection_performed privado. El guard de medios usa leases/readers para impedir borrado durante lectura.
- **Decision**: Adaptador de extracción que abre la fuente retenida con lease, busca keyframe anterior con PyAV y decodifica hasta el PTS exacto del recibo usando su base temporal. Compartir la conversión aprobada sin cambiar sus parámetros. Validar intervalo, geometría y bbox servidor; rechazar datos de píxeles/bbox/URL enviados por el cliente. Ante caja predicha válida extraer ese cuadro exacto y marcar `observation_kind=predicted`; no presentarla como medición ni volver a detectar escena. Sin correspondencia/recorte válido: estado unavailable y alternativas con tiempos solo elegibles tras selección expresa.
- **Rationale**: Mantiene la fidelidad del instante sin nuevo YOLO y evita cargar todo el video en memoria. Seek aproxima un keyframe; la coincidencia se verifica después, no se presupone. La extracción se ejecuta en un subproceso efímero PyAV-only, iniciado por el único worker de inspección; el padre mantiene el lease y watchdog de5s incluido arranque, termina/recolecta el hijo al vencer/cancelar y elimina su salida temporal. El hijo no importa app.main, Torch ni loaders/OCR; argumentos estructurados sin shell y sin ventana en Windows. Antes de publicar se verifican PTS racional, dimensiones, bbox, tamaño máximo y vigencia del contexto/padre. Un reloj dentro de un hilo no basta para detener native decode bloqueado. Los límites 300 cuadros/5 s devuelven error local si no permiten llegar al destino; nunca caen silenciosamente a otro cuadro.
- **Alternatives considered**: Guardar cada cuadro completo eleva disco/privacidad; decodificar siempre desde cero empeora consultas tardías; FPS nominal rompe VFR. La marca de predicción se consulta privadamente, sin cambiar FrameSlice legacy.
- **Fuente primaria**: [PyAV InputContainer.seek](https://pyav.org/docs/develop/api/container.html#av.container.InputContainer.seek), guía de seek desde keyframe seguido de decode. La documentación pública consultada identifica versión antigua; verificar el comportamiento con la dependencia fijada 19.0.2 mediante fixtures, no cambiar de versión para seguir la documentación.

## R4. Cola de inspección y estabilidad

- **Decision**: POST rápido valida y deduplica antes de encolar. Un worker acotado extrae el recorte fuera del lock de SQLite y reutiliza el EnrichmentProcessor ya cargado; solo las llamadas a modelos adquieren `progressive_slots`. Los estados parciales completan atributos/placa sin cambiar identidad ni imagen base. Recursos con asset_id/ruta estables; blob y zoom se asocian al contexto, no a revisiones globales. Cerrar/seek cancela entrega/polling; el trabajo aceptado puede terminar dentro de su cuota y reutilizarse. Fallos terminales no se reintentan en bucle.
- **Rationale**: Evita timeouts de gateway, doble inferencia tras POST perdido y carreras de resultados. La caché pertenece al contexto, no al primer resultado de la identidad.
- **Alternatives considered**: Extracción/inferencia síncronas retienen petición y agravan interrupciones; cancelar el worker al cerrar impide reutilización y complica carreras de archivos.
- **Recuperación**: Reencolar preparing sin crop publicado si los límites/padre siguen válidos; reutilizar crop inmutable verificado. Un processing interrumpido pasa a failed/inspection_interrupted sin repetir automáticamente OCR. Reabrir el contexto devuelve su estado; reintento técnico será una acción expresa futura solo si el contrato lo añade.

La expiración de cada contexto se fija al primer POST aceptado y no se renueva. Tras vencer su TTL propio, borrar assets/resultados y conservar solo clave de dedup/ID/expiración hasta vencer el padre. POST repetido de esa clave devuelve410 inspection_expired sin recrear ni ejecutar modelos. Esos tombstones cuentan entre las128 admisiones por job; cuota de bytes se libera al borrar archivos, cuota de admisiones solo al retirar el padre. Así el límite sigue siendo duro y una ausencia OCR no se recalcula por reabrir.

## R5. Cruce finito, sentido y tiempo

- **Evidencia**: `progressive_counting.py` guarda solo signo por track y suma A_to_B+B_to_A; no intersecta el segmento. El endpoint actual calcula/muta al leer. El nuevo diseño no cambia ese contrato legacy.
- **Decision**: Ruta separada `/playback/directed-count`. Definir signos mediante `cross(B-A,P-A)`; `negative_to_positive` sigue la normal `(-dy,dx)` en píxeles fuente, `positive_to_negative` la opuesta. A/B nombran extremos, no lados de circulación. Para una línea horizontal de izquierda a derecha, negativo→positivo apunta hacia abajo en la imagen.
- **Algoritmo decidido**: Solo centros de raw_bbox medidos. Guardar última posición medida, último lado no nulo y contacto finito pendiente durante secuencias sobre la línea. Distancia firmada en píxeles; cero numérico con epsilon=0.000001 píxeles. Contar al confirmar cambio entre lados no nulos con intersección del trayecto medido con el segmento inclusivo y sentido correcto. Contacto seguido de retirada al mismo lado no cuenta; nacimiento sobre la línea no supone origen previo. Predicciones no cambian estado. Una ida inversa o por prolongación no consume elegibilidad para un posterior cruce correcto. Cada evento se fecha en start_us de la medición confirmatoria, sin interpolar un pasado no observado.
- **Rationale**: Representa exactamente el segmento y la evidencia disponible. Cada identidad aporta a lo sumo un evento por revisión; no confundir track_id con total. La flecha se calcula en geometría fuente para no deformarla en 16:9.
- **Alternatives considered**: Signo respecto a recta infinita cuenta fuera de extremos; contar predicciones puede sumar cruces luego desmentidos; sumar ambos sentidos contradice la aclaración del usuario.

- **Refinamiento A1 aprobado**: La elegibilidad de cruce se evalúa únicamente con la clase medida en la observación que confirma el paso, normalizada con strip/lower. Se admiten car, truck, bus, van, pickup, suv, sedan, hatchback, mpv, estate, bicycle y motorcycle; person, vacío y clases no catalogadas no suman cruces. Todas las mediciones conservan el estado geométrico de la trayectoria; un paso excluido por clase no consume la elegibilidad para un futuro cruce válido. Guardar class_key_at_crossing inmutable en el evento y no reevaluarlo con votos futuros, clasificación consolidada u OCR. Esta política no restringe el resumen: sus clases no catalogadas siguen visibles con requires_review. Reutilizar una taxonomía pura compartida, independiente de VEHICLE_CLASSES de enriquecimiento.

## R6. Revisión, reducer y editor previo

- **Decision**: PUT con generation/expected_revision y dirección obligatoria; misma configuración con revisión vigente es no-op, revisión obsoleta devuelve409. Tras respuesta perdida, GET permite verificar configuración antes de reintentar; no sobrescribir borradores con datos tardíos. DELETE usa revisión esperada y mantiene tombstone mínimo. Nueva revisión recalcula en worker sobre recibos persistidos, 200 cuadros por lote; GET solo consulta estado/eventos indexados. Para intervalos fuente semiabiertos, ready exige at_us<covered_until_us; igualdad con el inicio del siguiente cuadro pendiente no está cubierta. La UI limita la consulta a un instante <available_until_us (habitualmente el inicio del cuadro pintado/last_frame_start_us). Con prefijo vacío solo at_us=0 devuelve pending/null o disabled/0, sin afirmar cobertura. Eventos únicos `(job,revision,track)`, con tiempo<=at_us. Versiones anteriores se eliminan por lotes tras quedar inaccesibles, sin tocar los eventos legacy.
- **Rationale**: Evita una transacción larga o una consulta periódica que haga trabajo creciente. La UI distingue watermark del análisis y del conteo y no dibuja datos futuros. Valores anteriores solo se conservan con su tiempo/revisión y estado «actualizando», nunca como total del nuevo seek.
- **Editor**: El código actual monta `ProgressiveCountTools` tras media_available; no satisface edición antes de analizar. Extraer primer fotograma del File local antes del POST, guardar borrador por archivo y aplicar al job aceptado; fuente local no modifica modelos ni proporciona evidencia confiable al backend.
- **Alternatives considered**: Añadir direction opcional al endpoint antiguo dejaría ambiguo el valor both; mutar por GET dificulta pruebas, prioridades y concurrencia.
- **Fuente primaria**: [SQLite Transactions](https://www.sqlite.org/lang_transaction.html): un escritor simultáneo, transacciones no anidadas. Reusar conexión/lock y transacción de publish; no abrir BEGIN dentro de on_publish.

## R7. Inventario por clase

- **Evidencia**: `VideoJobStore.summary()` cuenta filas de video_detections; no identidades únicas. `p_tracks.payload.class_name` puede cambiar por enriquecimiento. VEHICLE_CLASSES limita elegibilidad OCR/atributos y excluye bicicleta/moto; no es la taxonomía del resumen.
- **Decision**: Inventario independiente reducido en publish, exclusivamente por cuadros nuevos medidos. Normalizar clase con strip/lower; mantener car, sedan, suv, etc. separados. Ganador de identidad: mayor número de votos; empate por mayor confianza máxima observada; nuevo empate por class_key lexicográficamente menor. Contar cada identidad en una sola clase, sin sumar repetidas observaciones. No sumar confianzas flotantes.
- **Taxonomía explícita v1**: Clases vehiculares conocidas del registro de presentación, incluidas bicycle y motorcycle; person se excluye del total de vehículos y se declara `excluded_nonvehicle_tracks`. Claves desconocidas o vacías se conservan como «Clase no catalogada»/«Sin clasificar», con marca requires_review, sin perderlas ni asegurar su clasificación física; se incluyen como categoría explícita del total automatizado y se documenta esa limitación. Clasificar no equivale a reidentificar: identidades fragmentadas pueden duplicar un vehículo físico.
- **Rationale**: Independencia de línea/OCR y resultado reproducible aunque cambie el orden del lote. La suma de grupos elegibles, incluidas categorías sin clasificar, coincide con total_tracks.
- **Alternatives considered**: Usar /summary repite vehículos por cuadro; usar p_tracks depende de OCR; agrupar todos los subtipos como automóvil pierde clases solicitadas.

## R8. Migración y cobertura

- **Decision**: Tablas aditivas/índices y cursores persistidos; sin borrar ni reinterpretar tablas previas. Trabajos nuevos inicializan inventario antes de publicar. Trabajos progresivos antiguos se inspeccionan y reconstruyen en segundo plano una sola vez por política/generación, por lotes. Si no hay detection_performed, solo se aceptan observaciones respaldadas por filas medidas de video_detections consistentes; sin procedencia suficiente, capacidad unavailable/reanalysis_required. GET nunca inicia backfill.
- **Rationale**: Evita tratar predicciones antiguas como mediciones y evita falsos resúmenes definitivos. `analysis=complete` exige cursor completo antes de final; fallo/cancelación conservan parcial con cobertura. Backfill y reducer ceden el lock y sobreviven a reinicios.
- **Ciclo de vida**: Agregar explícitamente todas las tablas/rutas de derivados a cleanup/withdrawal; el código actual enumera tablas conocidas. Assets solo se publican tras rename atómico y revalidación del padre. Tombstones no retienen placas, atributos ni imágenes.

## R9. Etiquetas exportadas, fuentes y caché

- **Evidencia**: `ProgressiveExport` llama draw_box sin Track ID y ese helper solo dibuja bordes. `annotation_service.py` usa paleta/índices distintos y Hershey no cubre bien acentos. Una exportación ready de 009 seguiría sirviéndose si no se versiona.
- **Decision**: Renderer de cuadro completo exclusivo de exportación, con todas las cajas/Track ID/clase y paleta de `class_presentation.json`. Texto «Automóvil · #27» usando Pillow y su fuente escalable incluida; medir glifos españoles y tamaños de identidad seguros. Fallback de clase no catalogada con etiqueta legible sin copiar texto arbitrario ilimitado. Preferir encima, probar ubicaciones dentro del cuadro y líderes para etiquetas desplazadas; orden estable por Track ID y reutilizar colocación válida para reducir saltos. Minimizar solapamientos sin suprimir etiquetas en escenas extremas.
- **Caché**: Opt-in `renderer=vehicle-labels-v1` en GET/POST de exportación; variante y ruta de contenido privadas propias. Tabla de variantes separada; exportaciones antiguas no se presentan como etiquetadas ni se borran para fabricar un cache hit. Misma orquestación/worker y prioridades, sin segunda instancia de modelos.
- **Rationale**: Corrige descarga sin cargar el análisis principal ni depender de fuentes del equipo. La etiqueta representa clase observada del cuadro y Track ID, no la clase consolidada del resumen ni OCR.
- **Alternatives considered**: Añadir solo putText no resuelve acentos/densidad; etiquetas por índice cambian identidad; reutilizar MP4 ready antiguo incumple el objetivo; exportación automática reintroduce el coste eliminado.
- **Fuente primaria**: [Pillow ImageDraw](https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html), medición textbbox/text y soporte de fuentes. La web estable muestra versión13; usar solo APIs disponibles en el rango existente y verificar glifos con la instalación compatible, sin actualizar al major13.

El adaptador de preview de video usa metadatos propios `InspectionPlatePreviewMetadata` con inspection_id, plate_asset_id, track/frame, espacio plate-crop y transformación original→procesada. Reutiliza display_contrast/ejecutor acotado, no el DTO de imagen que exige source_id/enrichment_job_id/detection_id. Se conserva la cabecera X-Plate-Preview-Metadata con versionado explícito y parser distinto por origen; el de imágenes no cambia.

## R10. Contratos y UI heredados

- **Decision**: Rutas nuevas para inspección, capabilities, conteo dirigido y resumen. Mantener schemas/respuestas de rutas antiguas y activar etiquetas por query opt-in. Actualizar allowlist exacta del gateway, validadores y errores locales: 404 de una inspección/recurso no retira por sí solo el video; 401/403 de sesión o 410 del padre sí retiran conforme al flujo existente. GET no extrae, encola ni ejecuta modelos.
- **Rationale**: Evita romper clientes antiguos y separa «sin evidencia» de «sesión expirada». No se exponen URLs arbitrarias, disco ni credenciales.
- **Alternatives considered**: Reinterpretar TrackResult o el resumen legacy pierde correspondencia histórica; añadir propiedades a PlaybackState cerrado rompe sus lectores estrictos.

## Estado final de investigación

Todas las incógnitas bloqueantes están resueltas. Las decisiones de producto ya autorizadas se mantienen; los fallos de capacidad, límites y procedencia tienen resultados explícitos. Las cifras de latencia/calidad deberán verificarse durante implementación; esta investigación no ejecutó benchmarks ni atribuye nuevos FPS al diseño.

## R11. Referencia reproducible de rendimiento (U1)

- Decision: Crear el harness autocontenido y capturar publication-baseline.json en T001 antes de cambios de producto; T002 depende de ese paso. No requiere los fixtures/API que se crearán después.
- Rationale: Evita una comparación final sin test ni referencia anterior. Calentamiento+>=3 repeticiones, mismas entradas/parámetros/entorno, medianas y huellas separan captura previa de candidato.
- Alternatives considered: Crear la referencia al final mediría el propio candidato como base; abrir worktree o iniciar la comparación larga contradice el alcance. Si la referencia deja de ser comparable, registrar pendiente/fallo y no inventarla.
