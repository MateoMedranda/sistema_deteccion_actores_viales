# Contrato del gateway web —008

Diseño futuro. No sustituye la API autenticada existente. [Data model](../data-model.md), [schemas](schemas.json).

## Frontera de confianza y configuración

Entrada app.web.main:app, sin importar app.main global ni inicializar modelos/stores de inferencia. Se ejecuta en loopback; frontend/dist se sirve estático. Para remoto, HTTPS con ingreso privado/autenticado existente y conexión directa restringida al gateway. Una cookie de bootstrap y Origin NO autorizan por sí solos visitantes públicos. Una instancia corresponde a un operador/principal backend configurado; no hay multiusuario/selección de key_id desde el navegador.

WEB_BACKEND_URL, WEB_BACKEND_API_KEY y WEB_ORIGIN son servidor-only en .env.web. URL fija normalizada, sin path/query/fragmento/credenciales; HTTP solo loopback. WEB_ORIGIN exacto y Host coincidente; TLS upstream verificado, trust_env=false y redirects=false. No aceptar target/base_url/host/owner/key ni un backend alternativo enviados por el usuario.

## Sesión

- POST /web/session: JSON vacío, Origin exacto y X-UI-Request:1, dentro del ingreso autorizado. Sin cookie previa. Consulta GET /api/v1/web-policy con la clave configurada y genera una sesión solo si configura/autentica correctamente.
- 200 ready: WebSession con epoch, expires_at, csrf_token y policy. Cookie road_ui_session aleatoria256bits, host-only, Path=/, HttpOnly, SameSite=Strict y Secure para HTTPS. HTTP loopback local es la única excepción a Secure.
- 503 configuration_missing/configuration_invalid/upstream_unavailable,401 access_rejected. No emitir cookie utilizable ni exponer URL/key/Settings/cuerpos de excepción. Capacidades de modelos falsas en policy no equivalen a clave inválida: ready significa conexión autorizada.
- DELETE /web/session: cookie, Origin y X-UI-CSRF válidos;204, invalida RAM/cookie. Client retira evidencia y cancela consumos antes de renovar. Configuración de operador no se borra.
- RAM128 sesiones/TTL absoluto900s por defecto; no refresh. Máximo configurable definido en data-model. Agotamiento429 Retry-After:1, cleanup<=2s y cierre sin residuos.

CSRF256bits pertenece a sesión, no backend. Header constante X-UI-Request:1 en bootstrap y todas las llamadas JS; X-UI-CSRF en relay de datos y reset. Validar Origin en mutaciones y rechazar Sec-Fetch-Site cross-site/same-site cuando se reciba; no habilitar CORS del gateway. Host no se toma de X-Forwarded-* no confiable. No confiar en headers de identidad del visitante.

## Relay bajo /web-api

El sufijo coincide con el path del backend. ApiClient administrado usa origenActual+/web-api; rutas relativas de artefactos se resuelven solo en ese origen/prefijo. Modo anterior de ApiClient con clave directa permanece para clientes autorizados existentes.

Allowlist cerrada, IDs de un segmento [A-Za-z0-9][A-Za-z0-9_-]{0,127}; rechazar barras escapadas, traversal, dobles decodificaciones y rutas no canónicas antes de reenviar:

| Método | Sufijo backend permitido | Query |
|---|---|---|
| GET | /api/v1/web-policy | ninguna |
| GET | /health/image-policy; /health/live; /health/ready; /health/video-ready; /health/enrichment-ready | ninguna |
| POST | /api/v1/detections/images | ninguna; multipart image |
| GET | /api/v1/detections/{id}/original-image; /api/v1/detections/{id}/annotated-image | ninguna |
| POST | /api/v1/video-jobs | ninguna; multipart video, intención opcional |
| GET/DELETE | /api/v1/video-jobs/{id} | ninguna |
| GET | /api/v1/video-jobs/{id}/detections | page/page_size |
| GET | /api/v1/video-jobs/{id}/summary; /annotated-video | ninguna |
| GET | /api/v1/video-jobs/{id}/annotated-video/content | ninguna; medio nativo |
| POST | /api/v1/enrichment-jobs | JSON source, intención opcional |
| GET/DELETE | /api/v1/enrichment-jobs/{id} | ninguna |
| GET | /api/v1/enrichment-jobs/{id}/results | page/page_size |
| GET | /api/v1/enrichment-jobs/{id}/detections/{positiveInt}/plate-preview | profile ausente o display-contrast-v1 |
| POST | /api/v1/video-jobs/{id}/count-jobs | JSON línea |
| GET/DELETE | /api/v1/count-jobs/{id} | ninguna |
| GET | /api/v1/count-jobs/{id}/events | page/page_size |
| GET | /api/v1/count-jobs/{id}/annotated-video | ninguna; medio nativo |

En filas abreviadas /annotated-video lleva el mismo prefijo /api/v1/video-jobs/{id}. Paginación entera page>=1/page_size1..100, sin claves repetidas. No incluir cámaras, archivos libres, docs/admin o rutas genéricas. Origin correcto no amplía esta lista.

El gateway descarta X-API-Key/Authorization/Cookie/Host/Forwarded y headers de identidad recibidos del cliente para el upstream; agrega únicamente X-API-Key configurado y headers aprobados de contenido/intención/Range. El backend sigue autorizando propietario mediante Principal existente.

## Reproducción nativa y Range

Excepción solo para GET de los dos contenidos MP4 de la tabla: elemento video no puede enviar X-UI-CSRF. Requiere cookie válida y mismo origen mediante Host/Fetch Metadata, con Cross-Origin-Resource-Policy:same-origin, no CORS abierto y Cache-Control:no-store. No basta con conocer el ID.

Antes de abrir contenido, consultar GET del job correspondiente y comprobar estado completed y menor TTL; el endpoint de contenido vuelve a autorizar. Un único Range bytes=start-end o suffix, sintaxis acotada; multi-range se rechaza416. Reenviar If-Range válido y conservar200/206/416, Content-Range, Accept-Ranges, ETag/Last-Modified cuando proceda. Ninguna URL contiene sesión, CSRF o clave. Usuarios sin Fetch Metadata siguen protegidos por cookie, CORP y el ingreso privado; una mutación nunca utiliza esta excepción.

El cliente recibe metadata por la ruta de datos con CSRF y asigna src relativa validada. Su timer retira src al mínimo TTL aunque esté pausado. Error de medio consulta estado por GET autenticado para distinguir indisponibilidad/401/404/410, sin reejecutar POST. No conservar un Blob entero como vía principal. Conteo conserva el endpoint específico de003.

## Límites, errores y cierre

AsyncClient compartido: max_connections16, max_keepalive8; admisión16 solicitudes/2uploads, exceso429 Retry-After:1, sin cola ilimitada. Bloques<=64KiB. No cargar un cuerpo completo ni crear archivo/spool adicional en el gateway.

Cotas de entrada:
- JSON<=16KiB; sin cuerpo en GET/DELETE.
- Multipart limitado por policy.image.max_upload_bytes o policy.video.max_upload_bytes +64KiB de overhead. Content-Length orienta pero se cuentan bytes reales/chunked. Validación específica del archivo sigue en backend.
- Un cap privado de transporte no amplía límites backend.

Cotas de salida: JSON<=2MiB; placa PNG<=2MiB/headerASCII<=2048; originales/anotadas de imagen<=64MiB; MP4<=2GiB por artefacto con streaming, sin reservar ese tamaño en RAM. Límites de transporte configurables con valores validados para despliegues que amplíen límites backend. Rechazar antes de streaming cuando Content-Length/Content-Range informe exceso; si el exceso aparece tarde, cortar flujo y mostrar fallo, no éxito.

Deadlines totales por operación: imagen POST120s, video POST180s, otros JSON15s (sondeo10s), imagen/evidencia30s, placa10s, stream de medio60s por solicitud Range; siempre antes de sesión/recurso. Connect2s, espera de pool<=.05s y read inactivo30s no sustituyen deadline total. Cerrar respuesta upstream y liberar cupo en finally, incluso desconexión, timeout o cuerpo parcial.

Accept-Encoding:identity upstream; contenido inesperadamente comprimido no se retransmite con longitud incorrecta. Conservar solo Content-Type/Length válidos, no-store, Retry-After, X-Request-ID seguro, metadata de placa y headers Range autorizados. No reenviar Set-Cookie, Location, headers hop-by-hop, paths o excepciones. Configurar httpx/httpcore en WARNING o con redacción equivalente: sus logs de solicitudes no deben publicar la URL privada, headers, cookies o tokens; registrar solo identificadores seguros y desenlaces. Redirección upstream=>502 segura; timeout504, indisponibilidad502/503, exceso413, sesión401, CSRF/origen403, ruta/query inválida404/422. Headers seguros/cookie expiry también en errores.

## Intención y backend propietario

El flujo nuevo de video exige UUID por tentativa y header X-UI-Intent en upload/enriquecimiento de video. Enriquecimiento de imagen previo puede omitir intención y conserva su comportamiento; no ocupa los dos registros de intención de video. Gateway exige la sesión vigente y deriva Idempotency-Key upstream con HMAC(secreto efímero,session_id+operación+UUID), sin guardar cuerpo ni revelar secreto. Para cada sesión conserva la última intención por fase, incluso si llegó una respuesta upstream que el navegador pudiera haber perdido, hasta reemplazo explícito o TTL; no reutiliza una ya reemplazada y nunca crea nueva automáticamente tras respuesta perdida.

El upstream almacena la garantía en filas temporales según [backend-additions.md](backend-additions.md). Replay no extiende TTL. Reinicio/reset web invalida el contexto; no hay recuperación/historial entre sesiones.

## Acreditación requerida

Canario ausente de build/HTML/config/red/logs; ingress y solicitudes sin sesión; mismo/cross-origin, Host y CSRF; reset/epoch; allowlist/traversal/query/destinos; uploads chunked/límites/disconexión; origen ajeno/redirect; Range200/206/416/expiry; streams cerrados y cupos retenidos hasta finalizar trabajo real. Compatibilidad del cliente directo sigue probándose.
