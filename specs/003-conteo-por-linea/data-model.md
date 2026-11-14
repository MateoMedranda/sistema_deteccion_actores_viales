# Data Model: Conteo de actores por línea

## CountLine

| Campo | Regla |
|---|---|
| point_a, point_b | Coordenadas x/y finitas, normalizadas entre 0 y 1. |
| orientation | A→B; define A_to_B y B_to_A. |
| length | Debe ser mayor que cero. |

## CountJob

| Campo | Regla |
|---|---|
| count_job_id | UUID público aleatorio. |
| source_video_job_id | Pertenece al mismo propietario y está completed/no vencido. |
| owner_key_id | Aísla toda consulta y artefacto. |
| status | queued, processing, completed, failed o cancelled. |
| processed_frames, total_frames | Progreso no decreciente entre 0 y total_frames. |
| expires_at | No posterior al vencimiento del video origen. |
| output_path | Privada y solo existe en completed. |
| error_code | Código público seguro opcional. |

Transiciones: queued → processing → completed; queued/processing → failed o cancelled. Los terminales son inmutables; processing no vencido se reencola tras reinicio.

## CountEvent

| Campo | Regla |
|---|---|
| count_job_id, track_id | Únicos en conjunto; un actor se cuenta una vez. |
| class_id, class_name | Heredados de la detección fuente. |
| direction | A_to_B o B_to_A. |
| frame_index | Entero no negativo, ordenado. |
| video_time_seconds | No negativo. |

## CountSummary

| Campo | Regla |
|---|---|
| class_name | Clase publicada por el modelo. |
| direction | A_to_B o B_to_A. |
| total | Número de eventos confirmados. |

## Relaciones

Un CountJob contiene exactamente una CountLine, muchos CountEvent y un CountSummary agregado. Un CountJob pertenece a un VideoJob terminado. Los eventos se derivan de FrameDetection, sin crear detecciones nuevas.

