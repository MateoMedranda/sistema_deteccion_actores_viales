# Research: Exploración de imágenes y video

**Fecha**: 2026-11-21. **Estado**: decisiones de diseño cerradas; implementación y medidas pendientes.
**Fuentes de intención**: [spec.md](spec.md), constitución y comportamiento actual del repositorio. Tres investigaciones de solo lectura cubrieron gateway, video y frontend. No se cargaron modelos, cambiaron parámetros o procesaron medios privados.

## R1. Configuración protegida y frontera de acceso

**Decision**: Gateway web ligero FastAPI en app/web/, separado del proceso detector. Sirve frontend/dist y retransmite únicamente operaciones permitidas al backend fijo configurado por WEB_BACKEND_URL y WEB_BACKEND_API_KEY. El navegador utiliza /web-api y una sesión opaca; no recibe la clave ni la dirección privada del upstream. Un principal de backend por instancia del gateway, sin cuentas nuevas ni cambio de authenticate_api_key.

**Rationale**: ApiClient hoy transmite X-API-Key desde el navegador. Variables VITE_* se incorporan al cliente; renombrar el formulario a una variable pública no protege la clave. El proceso web no importa app.main global ni su lifespan y, por tanto, no duplica modelos. [Vite: variables de entorno](https://vite.dev/guide/env-and-mode).

**Alternatives considered**: secreto VITE_*; URL/clave por bootstrap público; proxy abierto; cargar un segundo servicio de inferencia. Se descartan por exposición, autorización o recursos.

**Condición de despliegue**: Por defecto loopback y operador local de confianza. Uso remoto exige ingreso privado/autenticado preexistente y acceso directo al gateway restringido. Origin/CORS/cookie emitida a cualquier visitante no sustituyen esa frontera. No se entrega un servicio anónimo apto para Internet. Instancias de propietarios distintos usan configuraciones/principales separados; el cliente no elige propietario o backend.

## R2. Sesión y transporte cerrado

**Decision**: Cookie host-only HttpOnly/SameSite=Strict, Secure en HTTPS, identificador aleatorio de256bits, RAM con128 sesiones y TTL absoluto900s. Bootstrap POST /web/session con mismo origen; emite csrf_token separado de la clave del backend. Relay de datos exige cookie y X-UI-CSRF; escrituras además Origin exacto. Reset invalida la sesión y su epoch. Ver [contrato de gateway](contracts/gateway.md).

**Rationale**: Sesión evita exponer la API key y vincula los consumos a un contexto finito. Host, Origin y Fetch Metadata complementan el ingreso autorizado. El token CSRF es de la sesión web, no credencial del backend. [OWASP CSRF](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html).

**Alternatives considered**: guardar secretos en localStorage, cookies con resultados o sesión sin vencimiento. No crear historial. El modo local HTTP permite Secure=false exclusivamente en loopback; remoto exige HTTPS.

## R3. Streaming y límites

**Decision**: Un HTTPX AsyncClient por lifespan web;16 conexiones,8 keep-alive,16 solicitudes admitidas y2 uploads simultáneos, sin cola ilimitada. Multipart en streaming con cotas verificadas; respuestas en bloques<=64KiB, cierre garantizado y deadline absoluto. trust_env=false, TLS verificado y redirects desactivados. HTTPX pasa de extra dev a dependencia runtime con el mismo rango existente, sin actualización masiva.

**Rationale**: Un cliente persistente evita conexiones repetidas y el cierre explícito evita fugas de streams. [HTTPX async/streaming](https://www.python-httpx.org/async/). Autorización ocurre antes de leer el upload; no hay segundo archivo intermedio en el gateway.

**Alternatives considered**: response.read completo, un cliente por fragmento o confiar solo en Content-Length. Se rechazan por memoria/limpieza.

## R4. Reproducción nativa sin una copia completa del video

**Decision**: Video y conteo usan URL relativa autorizada del gateway con cookie y Range de un solo intervalo; el relay admite esta excepción de medios sin header CSRF únicamente para los dos paths de contenido exactos. Aplica Host, sesión, Fetch Metadata cuando exista, CORP same-origin y no-store; consulta primero estado/TTL del recurso. Las llamadas de datos siguen exigiendo CSRF. No hay token en URL, API key ni destino arbitrario. Al ocultar Video se pausa y conserva currentTime; al expirar/reset se retira src.

**Rationale**: El panel actual descarga el MP4 entero a Blob; evitarlo limita memoria y permite búsqueda sin otra inferencia. HTTP Range conserva semántica de200/206/416. [MDN Range](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Range_requests).

**Alternatives considered**: copiar cada video a Blob o permitir cualquier ruta sin controles para un elemento multimedia. El contrato limita la excepción; no se amplía a JSON o mutaciones.

## R5. Estado independiente de los modos

**Decision**: ImageWorkspace y VideoWorkspace permanecen montados bajo el mismo sessionEpoch, ocultando el panel inactivo. Navegar solo cambia activeMode. Cada espacio tiene una generación y una fuente; sin persistencia de medios/credenciales ni historial. Estado de red interrupted se recupera con GET, no con nuevas creaciones.

**Rationale**: El cleanup actual de useLegacyJob cancela trabajos; desmontarlo al cambiar de pestaña violaría FR-002. React conserva estado según posición/tipo/key. [React: preservar estado](https://react.dev/learn/preserving-and-resetting-state).

**Alternatives considered**: render condicional que desmonta; guardar todos los trabajos en almacenamiento permanente. El refresco completo no promete recuperar trabajo ni repetir POST.

## R6. Zoom de una única escena

**Decision**: SceneViewport usa escenario de dimensiones naturales W*s por H*s con imagen y contornos porcentuales juntos; scroll interno, escala intrínseca hasta4, Ajustar=min(1,anchoDisponible/W,altoDisponible/H). Niveles Ajustar/100/200/400%, ancla conservada, arrastre a partir de6px CSS, teclado40px/Shift120px. Trazo de contornos en píxeles CSS, sin ampliar hitboxes. No interceptar zoom del navegador.

**Rationale**: Transformar una sola geometría conserva la proyección; los recortes permanecen en coordenadas canónicas. Pointer Events/captura solo durante arrastre unifican entradas. [MDN Pointer Events](https://developer.mozilla.org/en-US/docs/Web/API/Pointer_events).

**Alternatives considered**: escalar imagen y overlays por separado, generar otra imagen ampliada o depender de hover/pellizco. No son necesarios.

## R7. Paleta única y video limpio

**Decision**: Extraer sin cambiar valores el registro007 a app/domain/class_presentation.json, importado por frontend y cargado por helper Python. Empaquetarlo explícitamente como dato de app; las pruebas exigen13 clases y fallback #64748B. Vite permite únicamente ese JSON fuera de frontend, sin abrir la raíz que contiene .env. RGB→BGR explícito y bordes auxiliares blanco/negro. El video de análisis no incorpora putText; la leyenda queda fuera. La elegibilidad procede del servidor.

**Rationale**: Evita dos tablas divergentes. No cambiar colores de imagen ni detecciones. El artefacto de conteo003 conserva línea/totales específicos, sin añadir identificadores de vehículos.

**Alternatives considered**: copiar paleta manualmente, asignación por módulo/orden o render interactivo temporal en navegador. Esto último pertenece a la propuesta futura.

## R8. Estabilización causal de presentación

**Decision**: Primer candidato gated-ema-v1: filtro de(cx,cy,w,h), alphas[0.65,0.8,0.9,1] en ese orden, elegir primera caja entera/clamp con IoU>=0.90 respecto a la observación raw actual;1 devuelve raw. Estado solo de tracks presentes. Reinicios y métricas exactas en [protocolo](validation-protocol.md).

**Rationale**: No predice cajas ausentes ni toca FrameDetection, tracker, conteo o selección de evidencia. Permite limitar geométricamente el retraso; el gate temporal se mide de manera independiente, no se supone cero por escribir el mismo cuadro.

**Alternatives considered**: promedio de cuadros futuros, extrapolar durante huecos o One Euro Filter. Este último ofrece adaptación velocidad/jitter, pero añade calibración. [Artículo original One Euro](https://gery.casiez.net/publications/CHI2012-casiez.pdf). No se atribuye al artículo el gate específico de008.

## R9. Tiempo, finalización y cancelación reales

**Decision**: processing_phase aditivo distingue queued/frames/encoding/publishing/ready/failed/cancelled sin cambiar status histórico. Tras EOF se confirma el número real de cuadros; no forzar processed_frames a un total estimado. FFmpeg se supervisa con cancelación/TTL y el permiso se mantiene hasta terminar el proceso real. Publicación de archivo+detecciones bajo estado/TTL coordinados; métricas reflejan el desenlace efectivo.

**Rationale**: Hoy el100% por cuadros antecede a codificar, finish fuerza el total y no revalida TTL. El estado futuro no debe mentir. FFmpeg permite desactivar stdin y observar progreso estructurado; no es obligatorio fingir un porcentaje de codificación. [FFmpeg](https://www.ffmpeg.org/ffmpeg.html).

**Alternatives considered**: nuevo estado público que rompa clientes, porcentajes temporizados o liberar cupo al cancelar el HTTP.

## R10. Correspondencia temporal conservada

**Decision**: Mantener el MP4 CFR que ya genera VideoWriter. La referencia de evidencia es frame_index/output_fps del video procesado; no PTS exacto del original VFR. Nuevos metadatos confirmados solo para trabajos nuevos; históricos sin confirmación muestran cuadro/referencia desconocida. Mantener resolución/FPS/duración aprobados y validar conteo exacto de cuadros en fixtures.

**Rationale**: Los metadatos de entrada y la frecuencia configurada del escritor no reconstruyen PTS originales. [OpenCV VideoWriter](https://docs.opencv.org/4.x/dd/d9e/classcv_1_1VideoWriter.html).

**Alternatives considered**: rediseño VFR/remux y endpoint de contornos por tiempo. Fuera de008.

## R11. Enriquecimiento automático con idempotencia

**Decision**: Una intención de upload y una de enriquecimiento por tentativa. Header opcional Idempotency-Key para POST video/enriquecimiento; columnas nullable+índice único parcial por propietario en las filas existentes. Hash de bytes+MIME para upload, fuente normalizada para enriquecimiento. Replay conserva recibo original; GET obtiene estado actual. Gateway deriva una clave por sesión/ruta/intención y rechaza intenciones fuera de sesión/TTL.

**Rationale**: Actualmente POST siempre crea un trabajo. Una guarda frontend no resuelve pérdida de respuesta o dos solicitudes simultáneas. No se añade cola/tabla de historial; garantía dura el TTL original, sin renovarlo. Usar INSERT con columnas explícitas al migrar.

**Alternatives considered**: UUID nuevo en cada reintento, buscar solo por índice de UI o deduplicar eternamente por contenido.

## R12. Resultados y alcance futuro

**Decision**: Lista paginada25, solo página actual y ficha seleccionada. Validar track_id para video y conservar evidence_frame_indexes/evidence_frame_index que hoy el parser descarta. Consultar todos los resultados mediante paginación, sin reutilizar endpoints de crops exclusivos de imagen. La propuesta de pausa/selección directa sigue fuera de implementación.

**Rationale**: La vista actual muestra JSON y página1. summary.detections cuenta observaciones por cuadro, no vehículos distintos; no se usa como total de vehículos. eligible_track_count lo calcula el servidor.

**Alternatives considered**: descargar todas las trayectorias al navegador o inventar una lectura para el cuadro actual.

## Cierre de investigación

No quedan decisiones técnicas abiertas. Valores de filtros/recursos son hipótesis versionadas que deben pasar pruebas, no mediciones realizadas. Se mantienen pendientes externos006/007. El acceso remoto depende de un ingreso autorizado existente; el modo local no depende de añadir un sistema de usuarios. Los límites y los gates se conservan en los contratos; un fallo futuro de medición no se oculta como éxito.
