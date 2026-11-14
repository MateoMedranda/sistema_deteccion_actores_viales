# Data Model: Extracción de características y placas

## ImageDetectionSource

Registro temporal creado junto con una detección de imagen para que el enriquecimiento pueda usar los píxeles originales.

| Campo | Regla |
|---|---|
| `source_id` | UUID público; coincide con el `request_id` de la detección de imagen. |
| `owner_key_id` | Propietario autenticado; obligatorio en cada lectura. |
| `original_path` | Ruta privada aleatoria; nunca se publica por API ni logs. |
| `width`, `height`, `media_type` | Metadatos validados de la imagen original. |
| `detections` | Cajas y clases producidas por la detección base, con `detection_id` estable. |
| `expires_at` | No posterior a `ARTIFACT_TTL_SECONDS`; al vencer elimina imagen y registro. |

## EnrichmentJob

| Campo | Regla |
|---|---|
| `enrichment_job_id` | UUID público aleatorio. |
| `source_kind`, `source_id` | `image` o `video`; la fuente debe pertenecer al propietario y estar vigente. |
| `owner_key_id` | Aísla creación, consulta, cancelación y resultados. |
| `status` | `queued`, `processing`, `completed`, `failed` o `cancelled`. |
| `total_units`, `processed_units` | Progreso no decreciente; una unidad es una detección de imagen o un track de video elegible. |
| `created_at`, `updated_at`, `expires_at` | `expires_at = min(vencimiento fuente, ENRICHMENT_RESULT_TTL_SECONDS)`. |
| `error_code` | Código público seguro opcional, sin detalles del modelo ni datos sensibles. |

Transiciones: `queued → processing → completed`; `queued/processing → failed/cancelled`. Un trabajo de fuente vencida no publica resultados parciales. Tras reinicio, un `processing` vigente se reencola; uno vencido se limpia.

## EnrichmentUnit

Representa el vehículo analizado dentro de un trabajo.

| Campo | Regla |
|---|---|
| `unit_id` | Identificador interno único por trabajo. |
| `detection_id` | Para imagen, la detección original; para video, la mejor evidencia de un track. |
| `track_id` | Obligatorio para video; ausente para imagen. |
| `class_id`, `class_name` | Heredados de la detección base; la clase debe estar en la lista vehicular configurable. |
| `evidence_frames` | Para video, lista acotada y ordenada de fotogramas candidatos; para imagen, vacía. |
| `attribute_status`, `plate_status` | Estados independientes: `pending`, `processing`, `completed`, `failed`; placa además puede finalizar `not_detected` o `unreadable`. |

Una unidad puede conservar atributos aunque la rama de placa falle, y viceversa. Un `track_id` genera exactamente una unidad consolidada por trabajo.

## AttributeResult

| Campo | Regla |
|---|---|
| `unit_id`, `attribute_name` | Clave única por atributo configurado. |
| `label` | Valor emitido por el catálogo del manifiesto del modelo; no se inventan etiquetas. |
| `confidence` | Número finito entre 0 y 1. |
| `evidence_frame_index` | Fotograma elegido para video; nulo para imagen. |
| `model_manifest_id` | Versión/checksum no secreto del modelo y preprocesamiento usados. |

## PlateResult

| Campo | Regla |
|---|---|
| `unit_id` | Una salida consolidada de placa por unidad. |
| `status` | `read`, `unreadable`, `not_detected` o `failed`. |
| `bbox_relative` | Caja de placa normalizada respecto al recorte vehicular; presente solo cuando se localiza placa. |
| `localizer_confidence`, `ocr_confidence` | Entre 0 y 1; se preservan como evidencia no sensible. |
| `plate_text` | Dato sensible; presente solo cuando estado es `read`, nunca se registra en logs. |
| `used_enhancement` | Indica si hubo un único reintento conservador por baja confianza. |
| `evidence_frame_indexes` | Fotogramas usados en consenso del video; nunca implica identidad real. |

## PlateCandidate (interno y temporal)

No se expone como historial público. Mantiene el resultado de OCR original y, si aplica, su único reintento mejorado: texto, confianza, calidad del recorte, confianza del localizador y fotograma. Se elimina junto con el trabajo. La consolidación acepta una lectura solo con consenso suficiente y umbral configurado; no corrige texto por patrón.

## ModelManifest

| Campo | Regla |
|---|---|
| `component` | `attribute_extractor`, `plate_localizer` o `plate_reader`. |
| `version`, `weights_checksum` | Identifican el componente sin revelar ruta o secreto. |
| `labels`, `input_spec`, `thresholds` | Catálogo, preprocesamiento y umbrales reproducibles. |
| `device` | Dispositivo configurado, documentado para mediciones. |

## Relaciones y retención

Un `EnrichmentJob` pertenece a una `ImageDetectionSource` o un `VideoJob`; contiene muchas `EnrichmentUnit`; cada unidad contiene muchos `AttributeResult` y un `PlateResult`. La fuente, candidatos y resultados se eliminan al vencer el menor TTL. Las filas expiradas conservan solo el mínimo necesario para responder `410` al mismo propietario, sin texto, recortes ni rutas.
