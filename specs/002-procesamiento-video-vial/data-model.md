# Data Model: Procesamiento vial por video

## VideoJob

| Campo | Tipo | Reglas |
|---|---|---|
| `job_id` | UUID | Identificador público aleatorio. |
| `owner_key_id` | string | Principal autenticado; se usa para aislar toda consulta. |
| `status` | enum | `queued`, `processing`, `completed`, `failed`, `cancelled`. |
| `progress_percent` | integer | Entre 0 y 100; solo aumenta durante `processing`. |
| `processed_frames` | integer | No negativo; nunca supera `total_frames`. |
| `total_frames` | integer | Validado, máximo 3600. |
| `input_metadata` | VideoMetadata | No contiene rutas internas. |
| `created_at`, `updated_at`, `expires_at` | timestamp UTC | `expires_at` controla limpieza. |
| `started_at`, `completed_at` | timestamp UTC opcional | Reflejan el ciclo de ejecución. |
| `error_code` | string opcional | Solo código público seguro. |
| `cancel_requested_at` | timestamp UTC opcional | Señal cooperativa de cancelación. |
| `result` | VideoResult opcional | Solo existe en `completed`. |

### Transiciones válidas

```text
queued → processing → completed
queued → cancelled
queued → failed
processing → cancelled
processing → failed
```

Al reiniciar, un `processing` no vencido se devuelve a `queued`. Los estados terminales no cambian.

## VideoMetadata

| Campo | Regla |
|---|---|
| `media_type` | `video/mp4`. |
| `container` | MP4 verificado. |
| `codec` | H.264 verificado. |
| `size_bytes` | ≤104857600. |
| `duration_seconds` | >0 y ≤120. |
| `width`, `height` | Positivos y ≤1920×1080. |
| `fps` | >0 y ≤30. |
| `total_frames` | >0 y ≤3600. |

## FrameDetection and Track

| Campo | Regla |
|---|---|
| `frame_index` | Entero desde 0. |
| `track_id` | Entero positivo, único dentro de un trabajo mientras el seguimiento persista. |
| `class_id`, `class_name` | Clase publicada por el modelo. |
| `confidence` | De 0 a 1. |
| `bbox` | Coordenadas normalizadas dentro del fotograma. |

Una detección pertenece a un `VideoJob`. ByteTrack puede crear un nuevo `track_id` tras oclusión prolongada o salida de escena; no se reclama identidad real de personas o vehículos.

## VideoResult

| Campo | Regla |
|---|---|
| `summary_by_class` | Por cada clase: `detection_count` y `unique_track_count`. |
| `annotated_video` | URL pública temporal, tipo `video/mp4`, vencimiento a 60 minutos. |
| `frame_count` | Igual a `processed_frames` al completar. |
| `processing_time_ms` | Tiempo total no negativo. |

## VideoArtifact

| Campo | Regla |
|---|---|
| `artifact_id` | Valor aleatorio no predecible. |
| `kind` | `input` o `annotated_output`. |
| `job_id` | Asociación exclusiva con el trabajo. |
| `expires_at` | Entrada: al estado terminal; salida: 60 minutos tras completarse. |

## Página de detecciones

| Campo | Regla |
|---|---|
| `items` | Detecciones del trabajo en orden por `frame_index`, luego `track_id`. |
| `page` | Desde 1. |
| `page_size` | Entre 1 y 100; predeterminado 50. |
| `total_items` | Total de detecciones aún disponibles para el trabajo. |
| `total_pages` | Redondeo superior de `total_items/page_size`. |
