# Quickstart: Validación de procesamiento vial por video

## Prerrequisitos

- Python 3.12 y dependencias del proyecto instaladas.
- FFmpeg y ffprobe disponibles en `PATH`; registrar sus versiones en la evidencia.
- Pesos del modelo aprobados, configuración privada y una API key de prueba.
- Un MP4/H.264 controlado y autorizado de hasta 2 minutos, 100 MiB, 1080p y 30 fps.
- Opcionalmente, 20 videos viales autorizados de referencia para la prueba de rendimiento.

## Configuración local

1. Copiar `.env.example` a `.env` fuera del control de versiones y configurar pesos, credenciales y dispositivo.
2. Configurar los límites de video, timeout, concurrencia, directorio temporal y ruta de SQLite documentados en [data-model.md](data-model.md).
3. Instalar dependencias y ejecutar el servicio:

   ```powershell
   uv sync --extra dev
   uv run uvicorn app.main:app --reload
   ```

4. Confirmar que `GET /health/live` y `GET /health/ready` responden correctamente.
5. Confirmar además `GET /health/video-ready`; devuelve `200` únicamente cuando modelo, FFmpeg y ffprobe están disponibles.

## Escenarios de validación

### 1. Carga asíncrona válida

1. Enviar el MP4/H.264 a `POST /api/v1/video-jobs` con `X-API-Key`.
2. Confirmar `202`, `job_id` único y estado `queued`.
3. Confirmar que la respuesta llega sin esperar el procesamiento total y en ≤2 s.

### 2. Progreso, resultado y detalle

1. Consultar `GET /api/v1/video-jobs/{jobId}` hasta estado terminal.
2. Durante `processing`, comprobar que el progreso aumenta y no supera 100.
3. En `completed`, verificar el resumen por clase y la URL temporal de video anotado.
4. Consultar `GET /api/v1/video-jobs/{jobId}/detections?page=1&page_size=50` y comprobar `frame_index`, `track_id`, clase, confianza y caja.
5. Recuperar el video anotado con la misma credencial y confirmar las cajas, etiquetas y IDs.

### 3. Validación y autorización

1. Intentar cargar archivo no MP4, MP4 sin H.264, archivo corrupto, mayor a 100 MiB, mayor a 2 minutos, 1080p, 30 fps o 3600 cuadros.
2. Confirmar que cada caso retorna un error seguro antes de crear trabajo o guardar archivo.
3. Repetir la carga sin clave o con clave inválida; confirmar rechazo antes de analizar multipart.

### 4. Cancelación y recuperación

1. Crear un trabajo largo controlado y solicitar `DELETE /api/v1/video-jobs/{jobId}` durante `queued` y durante `processing`.
2. Confirmar `cancelled`, ausencia de salida anotada y limpieza de entrada/parciales.
3. Crear un trabajo, reiniciar el servicio antes de que termine y confirmar que se reanuda de la cola temporal sin cruzar propietario, progreso ni resultado.

### 5. Vencimiento, aislamiento y rendimiento

1. Esperar 60 minutos o usar una TTL de prueba para confirmar que el video anotado y sus metadatos expiran correctamente.
2. Intentar consultar, cancelar o recuperar artefactos con otra credencial o `job_id` inexistente; confirmar que no se revela información.
3. Ejecutar los 20 videos de referencia con concurrencia documentada y registrar hardware, modelo, ByteTrack, FFmpeg, configuración no secreta, tiempos por video/fotograma, memoria, errores y p95.
4. Confirmar que al menos 95% termina en no más de dos veces su duración original.

## Pruebas automatizadas

```powershell
uv run pytest --basetemp .pytest-tmp-video --cov=app --cov-report=term-missing
```

Los resultados esperados y respuestas se documentan en [openapi.yaml](contracts/openapi.yaml).

## Evidencia local ejecutada

El 2026-11-12 se validó con FFmpeg/ffprobe 9.0.2 y un MP4/H.264 sintético de 64×48 px, 10 fps y
1 segundo: carga `202`, finalización asíncrona, detecciones paginadas y recuperación de MP4 anotado.
La evaluación de rendimiento con 20 videos viales autorizados continúa pendiente; el video sintético
no se usa como evidencia de rendimiento ni de calidad del modelo.
