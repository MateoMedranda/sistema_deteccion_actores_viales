# Contratos externos —video-count-lines-v1

Diseño aditivo, pendiente de implementación. `schemas.json` es la fuente de formas cerradas; las invariantes de grafemas, normalización, unicidad, cobertura e idempotencia requieren validación semántica adicional de data-model.md. `examples.json` distingue ejemplos válidos, negativos de forma y negativos semánticos. `openapi-additions.yaml` referencia esos esquemas y no redefine contratos009/010.

## Operaciones nuevas

Prefijo `/api/v1/video-jobs/{job_id}/playback/count-lines`:

| Método/ruta | Entrada | Resultado | Efectos |
| --- | --- | --- | --- |
| GET colección | query generation obligatoria | 200 Collection | Solo lectura: configuración, protocolo, límites efectivos, colores, importación ofrecida y TTL |
| PUT colección | cuerpo CollectionWrite; sin query | 200 Collection | Reemplazo atómico del conjunto por CAS; crea/edita/elimina solo diferencias |
| GET /counts | query generation,revision,at_us obligatorias | 200 CountSnapshot | Solo lectura de todos los totales al mismo instante fuente |
| POST /import-legacy | cuerpo LegacyImport; sin query | 200 Collection | Importación única/idempotente de un segmento010, sin inferencia ni scan completo |

No hay DELETE/PATCH ni rutas arbitrarias por UUID en esta versión. Un conjunto vacío explícito por PUT retira sus líneas; tombstones evitan recrear IDs eliminados. UUID cliente estable y CAS cubren reintentos y borradores anteriores a la carga. Un conflicto se concilia con GET; no reenviar una colección antigua sobre la revisión nueva de forma automática.

La colección contiene protocol=video-count-lines-v1, policy_version=finite-center-both-v1 y mode=both, revisión, líneas ordenadas, límites, admitted_count (incluye IDs eliminados), colores iniciales e información de importación. No acepta dirección; enviarla es422 por propiedad adicional. Las cantidades no duplican todos los metadatos: corresponden exactamente a los IDs/revisiones de la colección consultada. Un cliente que no posee esa colección la recupera primero.

## Temporalidad y estado

Revisión de configuración independiente del progreso. Cada valor: ID de línea, revisión geométrica, status pending/ready/unavailable, result_scope building/partial/final, covered_until_us, valid_until_us exclusivo, total entero o null y código seguro. Si ready, el número es exacto en [at_us,valid_until_us), donde el extremo es el mínimo de siguiente evento estrictamente posterior, cobertura y prefijo. Pending/unavailable tiene total=null y extremo=at_us; no permite reutilizar cantidad. Cantidad0 solo con ready. Final se refiere a cobertura completa de esa línea, no solo al estado terminal del video. El total de cada línea es histórico hasta at_us; no sumar tarjetas como inventario de vehículos físicos.

Si at_us es el extremo exclusivo disponible, devolver409; con prefijo vacío at_us0 produce pending/null. No usar FPS nominales para elegir posición; el frontend solicita start_us del cuadro pintado. Un dato listo del instante anterior no se presenta como cantidad del nuevo cuadro mientras llega su respuesta.

## Validación y capacidad

- Todos los objetos cerrados, números finitos/seguros, sin coerción de bool a entero ni coordenadas.
- Names: máximo1024 codepoints en transporte y2048 bytes UTF-8; semántica1–60 grafemas, NFC, espacios normalizados, sin controles inseguros y unicidad casefold preservando acentos. JSON Schema maxLength no prueba grafemas.
- Colores #RRGGBB; canónicos mayúsculos; unicidad semántica y paleta de32candidatos. Texto de tarjeta mantiene color neutro legible y contorno de línea; no aplicar color arbitrario al texto.
- Segmentos finitos0..1 con puntos diferentes. Identidad UUID única por lista; los IDs eliminados nunca vuelven a admitirse.
- Default10 líneas activas, máximo de protocolo32;128 admisiones por trabajo, incluyendo tombstones. Descriptor anuncia los valores efectivos. Ninguna mutación parcialmente válida se guarda.

## Errores previstos

Se mantiene envelope ApiError existente, con mensajes seguros y códigos sin nombres/valores sensibles.

| HTTP | Código / condición |
| --- | --- |
| 401/403 | Autenticación/autorización o CSRF/origen del gateway, igual que hoy |
| 404 | Padre ajeno/ausente según política existente; endpoint no soportado en servicio anterior se trata como capacidad local no disponible |
| 410 | artifact_expired para trabajo vencido/retirado |
| 409 | generation_changed, count_revision_changed, interval_not_ready |
| 409 | count_line_limit, count_line_admission_limit, count_line_deleted |
| 409 | count_name_conflict, count_color_conflict para conjunto final duplicado |
| 409 | legacy_import_conflict o legacy_line_unavailable |
| 413 | Cuerpo excede64 KiB en API/gateway |
| 422 | Query desconocida/repetida/entero inseguro, esquema cerrado, nombre o geometría inválidos |

Errores de cálculo por procedencia o límite de trabajo se devuelven dentro del CountValue como unavailable/total=null/error_code=reanalysis_required o count_work_limit; no convierten el video completo en fallido ni las otras tarjetas en cero.

## Gateway y compatibilidad

Añadir exactamente los cuatro pares ruta/método a ROUTES/classify y su query allowlist. Colección GET solo generation; counts GET generation/revision/at_us; PUT/POST sin query. Sin parámetros duplicados, rutas codificadas, dobles barras o dot segments. Preservar SafeInt y validación UUID; GET sin cuerpo. Aplicar64 KiB al nuevo family en proxy y bounded_video_detail de app.main, no-store a todas las respuestas y el límite JSON2 MiB vigente. No usar wildcard genérico para exponer rutas futuras.

Mantener sesión/origen/CSRF e inyección de APIkey únicamente en gateway; jamás trasladar secretos al browser. Integrar nueva ruta al router de API y nuevo servicio al lifespan. Autoridad de padre/generación/TTL tanto en operaciones como al commit del reducer fuera del lock.

El contrato010 de capabilities/directed-count y su enum direccional no se modifica. La interfaz nueva consulta su descriptor propio; si falta en un backend anterior, informa que no dispone de multilínea sin mentir usando un contador direccional como ambos sentidos. La importación nunca ocurre durante GET. Exportación, inspecciones, inventario e imágenes conservan contratos y comportamiento.

## Idempotencia y carrera

Una PUT aplicada incrementa revisión una vez. Repetición inmediata exacta de la última mutación con expected_revision anterior+hash reconocido retorna descriptor actual sin repetir trabajo. Cualquier revisión más antigua/divergente produce409 y recuperación. Una PUT no-op con revisión vigente no incrementa. POST import-legacy ya aplicado retorna el descriptor sin reimportar, incluso si se borró después la línea. Las verificaciones parent/TTL preceden toda conciliación.

El cliente no acepta una respuesta que no coincida con contexto/revisión/IDs/tiempo solicitados. Las mutations se serializan por colección; múltiples pestañas se arbitran por CAS del servidor. La forma de editar nunca depende del número de Track ID ni de un color como identificador.


Si se reduce una configuración de capacidad respecto a una colección ya guardada, conservarla y permitir edición de metadatos/eliminación; rechazar nuevas altas netas mientras exceda el nuevo límite. admitted_count incluye tombstones y permite explicar el motivo del rechazo. Los cambios operativos no borran líneas por sí mismos.
