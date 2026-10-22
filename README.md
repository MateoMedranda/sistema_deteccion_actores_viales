# Sistema de detección de actores viales

Microservicio para analizar una imagen vial con el modelo YOLOv10s aprobado y devolver detecciones
más una imagen anotada temporal. La primera iteración no procesa videos, cámara, placas, atributos,
historial persistente ni una interfaz web de producción.

## Configuración

1. Use Python 3.12 y cree un entorno virtual.
2. Instale las dependencias: `uv sync --extra dev`.
3. Copie `.env.example` a `.env` y configure `MODEL_WEIGHTS_PATH` y `API_KEY` con valores privados.
4. Inicie el servicio: `uv run uvicorn app.main:app --reload`.

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

## Seguridad y operación

- No registre ni comparta `API_KEY`, pesos del modelo o imágenes de usuarios.
- Despliegue detrás de TLS y un proxy con límites de solicitud.
- Los archivos y anotaciones se almacenan temporalmente y se eliminan al vencer el TTL.
- Ejecute `uv run pytest` antes de entregar cambios.
- La procedencia aprobada del modelo es `yolov10s_best.pt` evaluado en
  `Vehicle_Detection_System`; cambiar pesos, clases o umbral exige una nueva evaluación.
