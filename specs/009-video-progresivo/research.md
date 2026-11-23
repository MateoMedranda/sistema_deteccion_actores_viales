# Research — 009 Video progresivo

Fecha: 2026-11-22. Investigación de código y fuentes primarias, sin ejecutar modelos ni cambiar servicios. Referencia congelada: commit 431b6dfccea3fcaccf80feab9039c254604c0718. Tres agentes investigaron backend/timing, reproducción/gateway y enriquecimiento/medición; sus decisiones se consolidan aquí.

## R1. Separar disponibilidad y finalización

**Decision**: Recurso progresivo nuevo, asociado a un trabajo solicitado explícitamente en modo progresivo. Los estados legacy y sus contratos permanecen: completed continúa significando resultado anotado final listo. La disponibilidad progresiva puede ser completa aunque la exportación falle.

**Rationale**: video_processing acumula todas las detecciones; VideoJobStore.finish las publica juntas. Los endpoints, VideoWorkspace y el enriquecimiento exigen completed. Relajar ese estado global rompería clientes y conteo.

**Alternatives considered**: Cambiar completed para significar primer tramo; exponer listas legacy incompletas. Se descartan por incompatibilidad y denominadores engañosos.

## R2. Cronología de origen desde una sola decodificación

**Decision**: Puerto TimedVideoDecoder y adaptador PyAV, dependencia nueva av==19.0.2 fijada en backend/pyproject.toml y uv.lock durante implementación. Entrega BGR24 y PTS/time_base por cuadro; FFprobe permanece para admisión. Validar geometría, rotación y cronología del navegador, incluidos edit lists y origen no nulo, antes de publicar.

**Rationale**: PyAV expone PTS y su base de tiempo en los cuadros decodificados. Se conserva la misma entrada BGR al detector y tracker aprobados; frame_index/fps no representa VFR. Se comprobó distribución de 19.0.2 para CPython 3.12/Windows x64; no se instala en esta etapa. [Frames](https://pyav.org/docs/stable/api/frame.html), [tiempo](https://pyav.org/docs/stable/api/time.html), [distribución 19.0.2](https://pypi.org/project/av/19.0.2/).

**Alternatives considered**: Promedio FPS o CAP_PROP_POS_MSEC sin certificación no garantizan correspondencia. Escanear todos los cuadros con ffprobe y luego decodificar otra vez duplica trabajo y puede desalinear secuencias. Parsear showinfo mientras se consumen píxeles por pipes añade coordinación y backpressure.

**Gate**: Comparar píxeles/observaciones/Track ID con el camino aprobado. Una diferencia de decodificación o entrada al modelo necesita evaluación explícita y no se declara equivalente sin evidencia. Tiempos no representables terminan el análisis con error seguro y conservan el prefijo ya confirmado; no se inventa VFR ni se amplían restricciones de admisión.

## R3. Publicación transaccional de prefijo continuo

**Decision**: Un registro por cuadro, también vacío, intervalos [start_us,end_us), observaciones crudas y cajas de presentación ya calculadas. Se confirma el extremo de un cuadro con el siguiente PTS; el último usa duración validada del cuadro/stream. Lotes de hasta 15 cuadros o 0,5 segundos de cronología, lo que ocurra primero. Escritura atómica de lote, cuadros, evidencias referenciadas y watermark/revisión.

**Rationale**: El límite no puede derivarse del máximo recibido ni del total estimado. Los archivos se escriben y cierran antes de referenciarlos en la transacción; un rollback deja solo huérfanos eliminables. SQLite permite agrupar cambios atómicamente y un solo escritor; usar transacciones breves, bloqueo coherente y lecturas fuera de la inferencia. [SQLite](https://www.sqlite.org/lang_transaction.html).

**Alternatives considered**: Actualizar progreso por cuadro sin persistir resultados, o confirmar un cuadro por cada detección, confunde vacío con pendiente. Recalcular suavizado al retroceder cambia cajas y añade trabajo.

## R4. Original protegido como decodificador, canvas como salida visible

**Decision**: Reutilizar el MP4 aceptado a través de una ruta propia de origen, autenticada y con Range. Un elemento video silenciado, sin controles, PiP ni presentación nativa visible, sirve de decodificador. Un canvas presenta píxeles y cajas únicamente cuando mediaTime pertenece a un intervalo confirmado con anotaciones completas. Si JavaScript se retrasa, permanece el último cuadro admitido; no se revela el video crudo como fallback.

**Rationale**: seeking no es cancelable y los callbacks de cuadro son best-effort. Un video visible con corrección posterior de currentTime puede mostrar un cuadro futuro. La comprobación antes de dibujar protege la salida visible sin recodificación previa. [seeking](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/seeking_event), [callbacks](https://developer.mozilla.org/en-US/docs/Web/API/HTMLVideoElement/requestVideoFrameCallback).

**Alternatives considered**: MSE/fMP4 o HLS restringidos a fragmentos confirmados impedirían entregar bytes futuros, pero añaden fragmentación, alineación de dependencias de cuadros y otro almacenamiento. Se reservan para un cambio de diseño documentado si el gate de canvas no se satisface, no como un fallback automático que oculte fallos.

**Límite de confianza**: La restricción solicitada es de navegación/presentación dentro del reproductor. El propietario autenticado ya dispone del archivo que subió; Range del original no pretende ocultarle bytes futuros frente a herramientas de desarrollo. Ningún otro propietario recibe acceso. Audio permanece silenciado, igual que el resultado anotado actual; analizar/restaurar audio queda fuera.

**Gate**: Probar recepción de callbacks del decodificador no visible en navegadores soportados, carga de JS, canvas a FPS de origen, VFR, rotación y fullscreen del contenedor. No se promete precisión por la mera presencia de requestVideoFrameCallback; se mide la salida.

## R5. Transporte incremental acotado

**Decision**: Polling de estado progresivo cada 500 ms visible, una petición en vuelo; backoff 1/2/4/8 segundos en errores y suspensión en modo oculto. Páginas inmutables de observaciones por snapshot, cursor opaco y porción temporal. Presupuesto 1 MiB/página y máximo 1.000 observaciones, con cobertura de cuadros explícita y sin truncar detecciones.

**Rationale**: Mantiene las sesiones y los presupuestos cortos del gateway. El cliente valida identidad, versión y cobertura antes de habilitar/dibujar; una respuesta sin cambios no mueve el cursor de reproducción.

**Alternatives considered**: SSE y WebSocket añaden reconexión y deadlines largos sin necesidad de transportar video por ellos. Cargar todas las observaciones aumenta memoria y dificulta recuperar historia.

## R6. Enriquecimiento provisional y resultado final compatible

**Decision**: Capturar recortes originales antes de dibujar, durante el mismo decode. Una evidencia provisional temprana por Track ID y top-K global online con orden legacy (-confidence,frame_index). Al cerrar la fuente, finalizar usando exactamente las K mejores; cachear cada evaluación por evidencia/política. Máximo K+1 evaluaciones únicas por track, K igual al límite existente (habitualmente 3).

**Rationale**: Primeras K evidencias puede perder una placa buena tardía. La evidencia provisional no entra al consenso final salvo que pertenezca al top-K. unit_id persistente y (job_id,generation,track_id) sustituyen el ordinal detection_id, que hoy se asigna al ordenar tracks al final.

**Alternatives considered**: Reabrir video por unidad duplica decodificación; enriquecer cada cuadro dispara coste; volver a ejecutar al navegar es innecesario.

**Gate**: Reutilizar modelos, umbrales, semáforos, EnrichmentProcessor y consenso aprobados. Los datos finales de modo progresivo deben servir al adaptador legacy de enriquecimiento sin nuevas evaluaciones ni duplicar unidades. Recortes de vehículo/placa usan rutas de evidencia nuevas, no el plate-preview exclusivo de imágenes.

## R7. Cola y memoria acotadas

**Decision**: Un worker progresivo; cola durable de referencias, ventana en RAM de máximo 32 unidades y como máximo una evaluación activa. Se comparten semáforos de atributos/placa con legacy. Los candidatos no consumidos se sustituyen por top-K; evaluaciones ya realizadas se conservan solo hasta K+1 y su TTL. El productor no acumula cuadros mientras el enriquecimiento está lento.

**Rationale**: Paralelismo en CPU no equivale a aceleración. El scheduler cede entre unidades y evita pools por track; el coste provisional adicional debe compensarse y medirse, nunca asumirse gratuito.

**Alternatives considered**: Nuevas copias de modelos, concurrencia por vehículo ilimitada o descarte silencioso al llenar la cola.

## R8. Ciclo de vida y exportación

**Decision**: Recursos publicados propios con propietario, recibo y plazo original. Fallo técnico/timeout conserva el prefijo y terminaliza el agregado de enriquecimiento al drenar su cola o expirar. Cancelación/limpieza/cambio de archivo/denegación/vencimiento retiran acceso y detienen nuevas publicaciones. El janitor borra recursos sin lectores activos; los lectores observan retirada/deadline en cada bloque.

**Rationale**: Hoy release/recover/close y el worker borran recursos o reencolan desde cero. Separar recursos en vuelo de resultados confirmados; al reiniciar, un trabajo progresivo interrumpido pasa a partial_failed sin reanudar tracker ni borrar commits.

**Alternatives considered**: Conservar para siempre, extender TTL al publicar o reiniciar automáticamente inferencia mezclando identidades.

**Compatibilidad**: Exportación CFR actual y conteo permanecen con la semántica processed-cfr. El modo legacy sigue intacto. En progresivo, exportar al final utiliza el mismo recorrido de inferencia y las detecciones persistidas, sin esperar esa exportación para reproducir.

## R9. Seguridad del gateway

**Decision**: Nueva clase de medio progressive-source con descriptor explícito de preflight, distinta de native-final. Rutas exactas y consultas cerradas, GET/HEAD/Range/If-Range acotados y respuestas 200/206/416; no se relaja el completed del medio anotado. Estado y evidencias usan sesión/CSRF normales. Todo es same-origin, no-store y con autorización/TTL en backend.

**Rationale**: El proxy actual deriva preflight cortando /annotated-video y exige completed. Reutilizarlo indiscriminadamente abriría rutas ajenas. Range opera en bytes, no en tiempos de análisis. [Range](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Range_requests), [FileResponse](https://starlette.dev/responses/).

**Alternatives considered**: URL con clave, proxy genérico, CORS abierto o Blob completo del archivo en RAM.

## R10. Evidencia de aceptación, sin promesa de tiempo real

**Decision**: Congelar antes de ejecutar corpus y configuración de benchmark; mínimo tres pares alternados AB/BA por clip. Baseline 431b6df, candidato 009, mismas fuentes, modelos, límites y enriquecimiento habilitado. Informar tiempos por fase y conjuntos, esperas y errores; pico simultáneo del árbol de procesos, no suma de picos distintos. Gate tiempo <=110 %, RSS <=120 %; reproducción se evalúa aparte.

**Rationale**: Los ~8,2 FPS observados y el timeout del usuario no certifican una línea base. Los fixtures sintéticos validan causalidad y estado, no precisión ni coste de modelos reales. Se mantiene un caso de timeout 300 s y se permite al arnés un límite idéntico mayor para comparar clips largos sin cambiar .env privado.

**Alternatives considered**: Medir solo dibujo, sustituir fallos por éxitos, cambiar calidad, o cerrar el gate humano con capturas. Cinco participantes siguen siendo necesarios para SC-009.

## Resultado Phase 0

Decisiones técnicas resueltas. La dependencia nueva, los riesgos de cronología/canvas y los límites de coste tienen decisiones concretas y gates de implementación; no son resultados ya acreditados. No hay preguntas técnicas pendientes para escribir el diseño de Phase 1.


## Evidencia de implementación y decisión corregida

La copia desde video nativo produjo una discrepancia de píxeles frente a su marcador de tiempo bajo carga. La solución final admite VideoFrame inmutable por identidad y PTS; no se conserva la alternativa nativa visible. WebCodecs conserva los timestamps de chunks en los cuadros decodificados; el registro AVC define avcC como descripción del decoder. Fuentes primarias: https://www.w3.org/TR/webcodecs/ y https://www.w3.org/TR/webcodecs-avc-codec-registration/. El demux usa la API pública de https://github.com/gpac/mp4box.js/ (versión fijada2.6.0).

El decoder de referencia OpenCV usa swscale con contexto propio; su conversión del corpus no coincidía con los valores predeterminados de PyAV para video etiquetado BT.709. Se fijó el perfil compatible ITU601/BICUBIC, no un nuevo tratamiento de imagen. La comparación efectiva de3.611 cuadros dio cero diferencias. Fuente de contraste: https://github.com/opencv/opencv/blob/4.x/modules/videoio/src/cap_ffmpeg_impl.hpp. El resultado medido local, y no la fuente por sí sola, acredita paridad de este corpus.

WebKit Windows carece de VideoDecoder en el entorno evaluado. Los tests acreditan aviso/retirada segura y consulta de datos, sin acreditar reproducción allí. Formatos MP4 fragmentados o ediciones complejas permanecen incompatibles con la vista progresiva de esta entrega.
