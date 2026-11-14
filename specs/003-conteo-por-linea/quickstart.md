# Quickstart: Validación de conteo por línea

## Prerrequisitos

- La iteración 002 puede completar un video con detecciones y track_id.
- FFmpeg/ffprobe, modelo y API key están configurados.
- Un conjunto controlado de al menos 10 videos viales autorizados, con cruces conocidos y una línea esperada.

## Ejecución

1. Iniciar el servicio con uv run uvicorn app.main:app --reload.
2. Procesar un video hasta que su trabajo quede completed.
3. Crear un trabajo de conteo para el identificador de video enviando point_a y point_b normalizados.
4. Consultar el trabajo hasta completed; durante processing, verificar que progreso, eventos y totales acumulados solo aumentan.
5. Recuperar eventos paginados y confirmar un evento máximo por track_id.
6. Recuperar el video anotado y comparar línea, dirección y totales con el resumen.
7. Repetir con puntos inválidos, otra credencial, video vencido, cero cruces y actores que permanecen en el mismo lado.

## Evidencia esperada

- Confirmación del conteo en máximo 2 segundos.
- No duplicados para un track_id.
- Dirección y clase correctas para cada cruce controlado.
- Resultado visual temporal protegido y coherente.
- Métricas de duración, memoria, eventos y errores sin datos sensibles.

