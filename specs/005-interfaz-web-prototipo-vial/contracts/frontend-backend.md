# Contrato de integración frontend–backend

## Reglas comunes

- Base URL: valor de sesión HTTP(S), sin barra final. Las URLs relativas de artefactos se resuelven contra esa base.
- Autenticación: X-API-Key: clave en toda ruta funcional y descarga de artefactos.
- Errores: consumir únicamente code, message y request_id; no renderizar cuerpos crudos ni cabeceras. Estados 401/403, 404, 409, 410 y 503 se traducen a mensajes seguros.
- Medios protegidos: solicitar por fetch, convertir a Blob y revocar su URL local cuando deja de usarse.

## Imagen

| Operación | Solicitud | Resultado esperado |
|---|---|---|
| Analizar | POST /api/v1/detections/images, multipart/form-data, campo image | Detecciones, request_id y URL de imagen anotada. |
| Imagen anotada | GET /api/v1/detections/{requestId}/annotated-image | Binario autenticado para Blob. |

## Video

| Operación | Solicitud | Resultado esperado |
|---|---|---|
| Crear | POST /api/v1/video-jobs, multipart/form-data, campo video | 202 y job_id. |
| Consultar/cancelar | GET / DELETE /api/v1/video-jobs/{jobId} | Estado, progreso y resultado o cancelación segura. |
| Explorar | GET .../{jobId}/detections?page=&page_size=, /summary, /annotated-video y /annotated-video/content | Páginas, resumen y video temporal autenticado. |

## Conteo por línea

| Operación | Solicitud | Resultado esperado |
|---|---|---|
| Crear | POST /api/v1/video-jobs/{videoJobId}/count-jobs con point_a y point_b normalizados | Trabajo de conteo aceptado. |
| Consultar | GET /api/v1/count-jobs/{countJobId} y /events?page=&page_size= | Estado, progreso, eventos y totales por clase/sentido. |
| Video anotado | GET /api/v1/count-jobs/{countJobId}/annotated-video | URL relativa de artefacto; descargar autenticado. |
| Compatibilidad requerida | DELETE /api/v1/count-jobs/{countJobId} | Cancela un conteo del propietario o responde error seguro/estado terminal; necesaria para FR-010. |

## Enriquecimiento

| Operación | Solicitud | Resultado esperado |
|---|---|---|
| Crear | POST /api/v1/enrichment-jobs con source.kind (image/video) y source.source_id | Trabajo temporal de enriquecimiento. |
| Consultar/cancelar | GET / DELETE /api/v1/enrichment-jobs/{enrichmentJobId} | Estado y cancelación segura. |
| Resultados | GET .../{enrichmentJobId}/results?page=&page_size= | Atributos y placa; solo plate.status=read puede contener plate.text. |

## Compatibilidad CORS requerida

- El backend permite explícitamente los orígenes de desarrollo configurados, por defecto http://localhost:5173 y http://127.0.0.1:5173, y los orígenes autorizados de despliegue.
- Debe aceptar X-API-Key, métodos requeridos y solicitudes OPTIONS.
- No se permite Access-Control-Allow-Origin: * para rutas protegidas.

