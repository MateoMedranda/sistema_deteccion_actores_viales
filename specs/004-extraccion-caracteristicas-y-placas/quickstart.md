# Quickstart: Validación de extracción de características y placas

## Prerrequisitos

- Python 3.12, dependencias del proyecto y FFmpeg/ffprobe si se validarán videos.
- Pesos aprobados disponibles fuera del repositorio: modelo de atributos EfficientNet-B1, localizador YOLOv8n de placas y modelos de PaddleOCR.
- Un manifiesto de EfficientNet-B1 con etiquetas, tamaño, orden de color, normalización, umbrales y checksum.
- Una API key de prueba y datos viales autorizados: al menos 20 recortes/vehículos con referencia y 10 tracks de video con varios fotogramas. Las matrículas deben tratarse como datos restringidos.

## Configuración local

1. Copiar `.env.example` a `.env` fuera del control de versiones.
2. Configurar las rutas externas de pesos y manifiestos: `ATTRIBUTE_MODEL_WEIGHTS_PATH`, `ATTRIBUTE_MODEL_MANIFEST_PATH`, `PLATE_MODEL_WEIGHTS_PATH` y `PADDLE_OCR_LANG`; además de dispositivo, umbrales, TTL, directorios, concurrencia y clases vehiculares. No fijar rutas personales dentro del código.
3. Instalar dependencias y ejecutar la suite:

   ```powershell
   uv sync --extra dev
   uv run pytest --basetemp .pytest-tmp-enrichment-unique --cov=app --cov-report=term-missing
   ```

4. Iniciar el servicio y verificar salud:

   ```powershell
   uv run uvicorn app.main:app --reload
   Invoke-RestMethod http://127.0.0.1:8000/health/live
   Invoke-RestMethod http://127.0.0.1:8000/health/ready
   ```

5. Ejecutar un smoke test de los tres modelos con un recorte autorizado antes de habilitar el servicio como listo.

## Escenario 1: Imagen existente

1. Enviar una imagen a `POST /api/v1/detections/images` con `X-API-Key` y conservar el `request_id`.
2. Crear enriquecimiento mediante `POST /api/v1/enrichment-jobs` con `{"source":{"kind":"image","source_id":"<request_id>"}}`.
3. Confirmar `202`, identificador aleatorio, estado `queued` y vencimiento no posterior al de la fuente.
4. Consultar `GET /api/v1/enrichment-jobs/{enrichmentJobId}` hasta un estado terminal.
5. Consultar `GET /api/v1/enrichment-jobs/{enrichmentJobId}/results?page=1&page_size=50` y verificar atributos, estados independientes y salida de placa sin rutas internas ni URLs de recorte.

## Escenario 2: Video terminado

1. Procesar un video con la iteración 002 hasta que `GET /api/v1/video-jobs/{videoJobId}` informe `completed`.
2. Crear un trabajo con `{"source":{"kind":"video","source_id":"<videoJobId>"}}`.
3. Confirmar que cada `track_id` elegible produce un solo resultado consolidado y conserva los índices de fotogramas usados como evidencia.
4. Verificar que la placa se acepta solo cuando el OCR supera el umbral y el consenso; un desacuerdo debe devolver `unreadable`.

## Escenario 3: Seguridad, vencimiento y tolerancia a fallo

1. Repetir consultas con una API key distinta: deben devolver error seguro sin texto, evidencia ni confirmación de existencia.
2. Probar fuente inexistente, no terminada, vencida, sin vehículo y fuera de la lista elegible: no se crea trabajo.
3. Simular fallo de atributos y fallo de placa de forma separada: la rama exitosa permanece disponible y la fallida no filtra detalles internos.
4. Reducir TTL en entorno de prueba y comprobar que fuente, variantes de recorte y resultado dejan de estar disponibles al expirar.

## Evidencia de calidad y rendimiento

- Medir macro F1 de atributos, AP/IoU de localización de placa, exactitud completa de OCR, CER y tasa de lectura falsa.
- Comparar OCR original, reintento conservador y consenso por track. Ninguna lectura debe publicarse por corrección automática de formato.
- Registrar modelo/manifiesto, dispositivo, configuración no secreta, p50/p95 por rama y por track, memoria, errores y número de reintentos; excluir textos de placas y rutas privadas de logs e informes.
- Validar los contratos de [openapi.yaml](contracts/openapi.yaml) y las entidades de [data-model.md](data-model.md).

## Estado de validación de esta implementación

- La ruta de imagen, creación/consulta de trabajo y aislamiento entre API keys están cubiertos con adaptadores sin pesos reales.
- Antes de un smoke real debe resolverse la carga de PyTorch del equipo y ejecutar `uv run pytest tests/e2e/test_enrichment_model_smoke.py` con los pesos autorizados configurados.
- Una ejecución completa debe usar un directorio `--basetemp` nuevo, pues Windows puede bloquear bases SQLite de una ejecución anterior.
