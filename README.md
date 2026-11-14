# Sistema de detección de actores viales

Microservicio para analizar imágenes y videos viales con el modelo YOLOv10s aprobado. La API de
video registra un trabajo asíncrono, procesa los fotogramas, conserva las detecciones de forma
temporal y publica un MP4 anotado cuando concluye. Cámara, placas, atributos, conteo por línea,
historial permanente e interfaz web siguen fuera de alcance.

## Configuración

1. Use Python 3.12 y cree un entorno virtual.
2. Instale las dependencias: `uv sync --extra dev`.
3. Copie `.env.example` a `.env` y configure `MODEL_WEIGHTS_PATH` y `API_KEY` con valores privados.
4. Inicie el servicio: `uv run uvicorn app.main:app --reload`.

Para procesar video se requieren **FFmpeg y ffprobe 6 o superior** instalados y disponibles en
`PATH`; compruebe su instalación con `ffmpeg -version` y `ffprobe -version`. En Windows, instale
una distribución confiable, agregue su carpeta `bin` al `PATH` y reinicie la terminal. El servicio
acepta únicamente MP4/H.264 dentro de los límites declarados en `.env`; no cambie esos límites sin
medir memoria, latencia y cola.

La ruta de pesos debe apuntar al modelo aprobado. Si se requiere la variante local de Ultralytics
usada durante la investigación, configure `ULTRALYTICS_PATH` sin copiar sus fuentes ni sus pesos al
repositorio de este microservicio.

| Variable | Propósito | Regla de seguridad |
|----------|-----------|--------------------|
| `MODEL_WEIGHTS_PATH` | Archivo de pesos YOLOv10s aprobado | Ruta privada; no versionar ni publicar el archivo. |
| `ULTRALYTICS_PATH` | Variante local compatible, si se requiere | Debe ser una ruta controlada en el servidor. |
| `API_KEY` | Protege las rutas de análisis y artefactos | Usar un secreto largo, entregarlo por gestor de secretos y rotarlo. |
| `MODEL_CONFIDENCE_THRESHOLD` | Umbral entre 0 y 1 | Cambiarlo solo con evidencia de evaluación del modelo. |
| `MAX_UPLOAD_BYTES` y `MAX_IMAGE_PIXELS` | Límites de carga | Mantener límites conservadores en producción. |
| `ARTIFACT_TTL_SECONDS` | Vida de la imagen anotada | Reducirlo cuando la política de datos lo exija. |
| `MAX_CONCURRENT_INFERENCES` y `INFERENCE_DEVICE` | Protección de recursos | Ajustar según GPU/CPU documentada y memoria disponible. |

## Uso de la API

Envíe una imagen JPEG o PNG con una clave válida:

```powershell
curl.exe -X POST http://127.0.0.1:8000/api/v1/detections/images `
  -H "X-API-Key: $env:API_KEY" `
  -F "image=@C:\ruta\imagen.jpg"
```

La respuesta contiene las detecciones y una URL temporal protegida. Solicite esa URL con la misma
clave para ver la imagen anotada. Consulte el contrato completo en
`specs/001-deteccion-imagen-vial/contracts/openapi.yaml`.

### Video asíncrono

Envíe un MP4/H.264 con la misma clave. La respuesta `202` contiene un `job_id`; consulte su estado
hasta que sea `completed` y luego solicite las detecciones o el video anotado con esa misma clave.

```powershell
$headers = @{ "X-API-Key" = $env:API_KEY }
$job = curl.exe -s -X POST http://127.0.0.1:8000/api/v1/video-jobs `
  -H "X-API-Key: $env:API_KEY" -F "video=@C:\ruta\video.mp4" | ConvertFrom-Json
Invoke-RestMethod "http://127.0.0.1:8000/api/v1/video-jobs/$($job.job_id)" -Headers $headers
```

Rutas disponibles al completar el trabajo: `GET /api/v1/video-jobs/{job_id}/detections`,
`GET /api/v1/video-jobs/{job_id}/summary` y
`GET /api/v1/video-jobs/{job_id}/annotated-video/content`. Los archivos de entrada y salida se
eliminan al vencer `VIDEO_RESULT_TTL_SECONDS` o al detener limpiamente el servicio.

## Seguridad y operación

- No registre ni comparta `API_KEY`, pesos del modelo o imágenes de usuarios.
- Despliegue detrás de TLS y un proxy con límites de solicitud.
- Los archivos y anotaciones se almacenan temporalmente y se eliminan al vencer el TTL.
- Ejecute `uv run pytest` antes de entregar cambios.
- La procedencia aprobada del modelo es `yolov10s_best.pt` evaluado en
  `Vehicle_Detection_System`; cambiar pesos, clases o umbral exige una nueva evaluación.
