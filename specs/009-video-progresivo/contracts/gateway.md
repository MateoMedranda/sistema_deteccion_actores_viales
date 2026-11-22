# Gateway — ampliación 009

Conservar la frontera de confianza de [008](../../008-exploracion-imagen-video/contracts/gateway.md). Nada de credenciales en el navegador ni nuevas rutas genéricas.

## Allowlist nueva

| Clase | Método/sufijo | Query |
|---|---|---|
| video-upload actual | POST /api/v1/video-jobs | presentation ausente o progressive; solo esa clave |
| progressive-json | GET /api/v1/video-jobs/{id}/playback | ninguna |
| progressive-json | DELETE /api/v1/video-jobs/{id}/playback | ninguna |
| progressive-json | GET /api/v1/video-jobs/{id}/playback/frames | from_us,to_us,snapshot,cursor según contrato |
| progressive-json | GET /api/v1/video-jobs/{id}/playback/tracks | snapshot,cursor |
| progressive-json | GET /api/v1/video-jobs/{id}/playback/tracks/{positiveInt} | ninguna |
| progressive-source | GET/HEAD /api/v1/video-jobs/{id}/playback/source | ninguna |
| progressive-evidence | GET /api/v1/video-jobs/{id}/playback/tracks/{positiveInt}/evidence/{uuid}/{vehicle-or-plate} | ninguna |

IDs canónicos de un segmento; ninguna barra escapada, traversal, doble decodificación, clave duplicada, parámetro extra, owner/url/path enviado por el usuario. from_us=0 y snapshot=0 son válidos sintácticamente: no copiar la validación legacy de paginación que exige enteros positivos para todos los campos.

JSON y evidencia por JavaScript mantienen X-UI-Request y X-UI-CSRF, cookie de sesión y controles Host/Origin actuales. El source nativo GET/HEAD, exclusivamente, obtiene la misma excepción de headers JS que los MP4 actuales: cookie vigente, Host, Fetch Metadata cuando exista, CORP, backend propietario y mínimo TTL. No extender esa excepción a frames/tracks/DELETE o a cualquier archivo.

## Preflight y streaming

Sustituir la derivación genérica por split('/annotated-video') con descriptores cerrados de recursos: legacy conserva status=completed, progressive-source consulta playback y exige media_available, generación válida y now<expires_at. No relajar todas las fuentes nativas a status=processing. Backend vuelve a autorizar el contenido.

Range acepta un solo intervalo de bytes o suffix; preservar Range/If-Range y200/206/416, Content-Type, Content-Length, Content-Range, Accept-Ranges, ETag y Last-Modified. HEAD sigue las mismas comprobaciones, sin cuerpo. No redirects, compresión upstream ni destinos alternativos. El límite de source corresponde al archivo aceptado, sin convertir el relay en un proxy arbitrario.

JSON respuesta<=2MiB; el productor progressive se limita a1MiB por página. Evidencia<=16MiB por respuesta con validación de geometría/decodificación; no degradar evidencia a escondidas para pasar el tamaño: reportar la rama como no disponible con error seguro si una configuración admitida excede esa representación. Source se transmite en bloques<=64KiB sin Blob completo; los recortes sí pueden recuperarse como Blob pequeño revocable.

Budget JSON10s, evidencia10s y media60s por petición, siempre mínimo con TTL de sesión/fuente/evidencia. Verificar expiración y sesión entre bloques; liberar upstream y contadores también en cancelación/desconexión. La fuente estable permite nuevas peticiones Range autorizadas, sin extender vencimiento.

## Retirada e intención

presentation se incorpora a la huella de idempotencia y a la clasificación de intención; el mismo UUID con modo distinto no crea otro trabajo. El cliente no hace otro POST al recuperar un GET.

DELETE playback es mutación protegida por CSRF y retira el recurso autorizado aunque legacy ya esté completed/failed. Limpieza/cambio de archivo/inicio de otra generación invalida consumos y respuestas en frontend y solicita retiro de su fuente anterior. Si una respuesta de aceptación llega después del cambio, se retira el recurso recién conocido.

Revocar la sesión limpia inmediatamente los dos modos; rechazos de acceso no se tratan como una pausa de búfer. Al renovar sesión no se restaura automáticamente una selección de origen anterior.

## Alcance del bloqueo

El bloqueo temporal es una regla visible de la aplicación. El propietario puede recuperar bytes futuros de su archivo original autenticado; el tiempo procesado no funciona como autorización de bytes. Si se exigiera ocultarlos al propietario se necesitaría un cambio explícito a entrega por segmentos confirmados; no se pretende resolver con HTTP Range.
