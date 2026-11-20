# Contrato backend aditivo — 006

**Estado**: propuesto para implementación, no desplegado.
**Base**: contratos 001/004/005 y código de `81bc12d`; el commit `6f0243a` posterior añade diagnóstico/auditoría, sin cambiar estos contratos.

## Operaciones existentes conservadas

- `POST /api/v1/detections/images`: multipart `image`, autorización `X-API-Key`, respuesta 200 de detección; mismos errores 400/401/413/415/422/503.
- `POST /api/v1/enrichment-jobs`: `source.kind=image`, `source.source_id=request_id`; respuesta 202, consulta GET y cancelación DELETE existentes.
- `GET /api/v1/enrichment-jobs/{id}/results?page=&page_size=`: paginación de 1–100, mismo esquema existente. Orden final de imagen por detection_id. Mientras processing: lista vacía y total=0, no resultados incrementales prometidos.
- Cancelación mantiene 202 cuando hay transición; 409 terminal exige al cliente tratarlo como finalizado, no como trabajo activo.
- Readiness global de enriquecimiento mantiene 200 ready y 503 not_ready; se añaden capacidades por rama sin cambiar semántica del estado global.

## Respuesta de imagen extendida

Se conservan todos los campos anteriores. La versión nueva del servidor añade:

| Campo | Regla |
|---|---|
| `source_expires_at` | Fecha UTC efectiva para la fuente; no superior a la evidencia relacionada. |
| `original_image.url` | `/api/v1/detections/{request_id}/original-image`, sin credencial en URL. |
| `original_image.media_type` | `image/png`: píxeles canónicos, orientación aplicada, sin anotaciones ni metadatos privados. |
| `original_image.expires_at` | Misma vigencia efectiva de fuente. |
| `detections[].enrichment_eligible` | Booleano calculado desde la configuración real de clases elegibles, no por lista hardcodeada en frontend. |

`image.width/height/media_type` describe el canónico. El archivo original se valida por MIME/extensión/tamaño antes de normalizar; no se vuelve a tratar PNG canónico como si fuera el upload original. `bbox` usa píxeles canónicos, enteros y extremos máximos exclusivos, compartidos por anotación/crop. No devolver cajas fuera de rango ni fabricar un píxel para una región degenerada.

No añadir `track_id` a la detección estática ni alterar el null existente de enriquecimiento. Los IDs se asignan antes de filtrar por clase, después de validar cajas, y se preservan al enriquecer.

La extensión es aditiva para clientes existentes; nuevas respuestas mantienen sus campos anteriores. El frontend nuevo requiere este contrato para evidencia canónica garantizada. Frente a un servidor anterior, puede mostrar detecciones e imagen anotada, pero comunica incompatibilidad de evidencia en vez de inventar geometría o elegibilidad.

## Nuevo GET del original canónico

`GET /api/v1/detections/{requestId}/original-image`:

- Mismo `X-API-Key` y comprobación de propietario de la fuente existente.
- 200 binario PNG y `Cache-Control: no-store`. No incluir el nombre privado de archivo ni rutas del servidor; no usar redirección hacia un archivo público.
- 401 si credencial ausente/inválida; 404 si fuente desconocida o de otro propietario; 410 solo para el propietario de fuente conocida ya vencida.
- Fuente y anotación comparten vigencia efectiva. Su lectura no renueva TTL. Obtener bytes/archivo en coordinación con la purga para evitar una carrera entre comprobar acceso y abrir el recurso.
- Aplicar `no-store` también a las respuestas protegidas de evidencia y resultados afectadas; el cliente revoca blobs al vencer. No prometer revocación de bytes ya recibidos.
- No hay nuevo endpoint separado de recorte: el cliente usa la imagen canónica y geometría existente.

## Capacidades de enriquecimiento

`GET /health/enrichment-ready` conserva estado global y añade:

```json
{
  "status": "not_ready",
  "capabilities": {
    "attributes": "ready",
    "plate_localization": "unavailable",
    "plate_ocr": "unavailable"
  }
}
```

Capacidades seguras y públicas como el health actual, sin rutas ni excepciones. `ready` global exige detector y las tres capacidades disponibles. Un adaptador no configurado es unavailable, nunca ready por defecto.

Crear enriquecimiento no se bloquea solo por 503 del health global: aceptar si hay atributos o localización de placa útiles. Separar el guard de localización del guard de OCR para conservar evidencia cuando el lector no esté listo. Si ambas ramas útiles faltan, responder 503 `enrichment_unavailable` con el formato seguro existente, sin encolar un trabajo condenado a fallo. Validación de propiedad/fuente siempre se aplica y no expone capacidades privadas del dueño.

## Estados de placa e integridad

- `read`: texto permitido si existe lectura autorizada válida.
- `unreadable`: texto null/ausente; conservar bbox cuando haya localización válida.
- `not_detected`: texto null/ausente y sin bbox inventada.
- `failed`: texto null/ausente; conservar bbox si falló después de localizar. Error seguro permite explicar rama no disponible sin detalles internos.
- `bbox_relative` permanece normalizada respecto al recorte vehicular exacto, no a la imagen completa. No se cambia su significado para facilitar la UI.
- Sanear el mismo objeto antes de almacenarlo en `results_json`, tablas normalizadas o devolverlo. Validar estados duplicados plate_status/plate.status y confianzas.
- Cada unidad elegible tiene un resultado o fallo explícito con su detection_id. Un crop inválido no se silencia mientras processed_units aparenta completitud.

## Cancelación, vencimiento y limpieza

- queued -> processing -> completed/failed; queued/processing -> cancelled; expiración elimina evidencia y genera 410 del dueño.
- Finalización y fallo tardíos solo pueden modificar un trabajo processing vigente; cualquier estado terminal es inmutable.
- Cancelar limpia JSON y filas sensibles asociadas bajo la misma transacción. Cleanup elimina originales y resultados vencidos sin tráfico; tombstones mínimos preservan 410 del dueño, 404 ajeno.
- Revisar estado entre unidades y antes de persistir; no se exige interrumpir una llamada de modelo no interrumpible ya iniciada.
- `expires_at` del job sigue siendo el mínimo del TTL configurado y el vencimiento de fuente. El cliente utiliza el mínimo entre fuente, artefacto y job.

## Validación exigida

Contrato antiguo sigue pasando; contrato nuevo comprueba campos y ruta. Pruebas de acceso/TTL, orientación EXIF y geometría, elegibilidad configurable, ramas disponibles por separado, saneamiento de JSON/tablas/respuesta, cancel/finish y TTL/finish concurrentes. No modificar los contratos históricos para ocultar una regresión; describir en 006 las extensiones y mantener la documentación viva del servicio cuando se implemente.
