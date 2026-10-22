# Quickstart: Validación de detección vial en imagen

## Prerrequisitos

- Python 3.12.
- Pesos YOLOv10s aprobados y accesibles solo al proceso del servicio.
- Una clave de API de prueba almacenada fuera del repositorio.
- Imagen JPEG o PNG autorizada para pruebas y, opcionalmente, un conjunto de 20 imágenes de
  referencia para medir rendimiento.
- GPU/CUDA si se va a medir la meta de latencia; registrar el hardware y versiones usadas.

## Configuración local

1. Crear y activar un entorno virtual de Python 3.12.
2. Instalar las dependencias bloqueadas del microservicio, incluidas las requeridas para recibir
   cargas multipart, validar imágenes, ejecutar el modelo y probar la aplicación.
3. Configurar, mediante variables de entorno o un almacén local de secretos, como mínimo:
   - `MODEL_WEIGHTS_PATH`: ruta privada a los pesos YOLOv10s aprobados.
   - `API_KEY`: credencial de prueba para `X-API-Key`.
   - `MODEL_CONFIDENCE_THRESHOLD`: valor entre 0 y 1.
   - `MAX_UPLOAD_BYTES`, `MAX_IMAGE_PIXELS` y `ARTIFACT_TTL_SECONDS`.
   - `INFERENCE_DEVICE`: dispositivo documentado para la medición.
4. Iniciar el servicio y confirmar que `/health/live` responde correctamente y que
   `/health/ready` responde solo después de cargar los pesos.

## Escenarios de validación

### 1. Análisis exitoso

1. Enviar una imagen JPEG o PNG válida mediante `POST /api/v1/detections/images` con el encabezado
   `X-API-Key` y el campo multipart `image`.
2. Verificar respuesta `200` conforme a [openapi.yaml](contracts/openapi.yaml): identificador de
   solicitud, dimensiones, tiempo de procesamiento, lista de detecciones y URL temporal.
3. Recuperar la URL temporal con la misma clave de API.
4. Verificar que la imagen devuelta contiene, para cada detección, una caja, la clase y la confianza.

### 2. Sin detecciones

1. Enviar una imagen válida sin actores que alcancen el umbral.
2. Verificar `200`, `detections: []` y una imagen anotada válida sin cajas falsas.

### 3. Rechazos seguros

1. Enviar un archivo de texto, una imagen corrupta y una imagen que supere el límite configurado.
2. Verificar respectivamente los códigos definidos en el contrato (`415`, `422` y `413`).
3. Confirmar que las respuestas no contienen rutas locales, trazas ni la clave de API.

### 4. Autorización y aislamiento

1. Repetir una solicitud sin clave y con una clave incorrecta; ambas deben recibir `401`.
2. Enviar dos imágenes válidas consecutivas y confirmar que cada respuesta tiene un `request_id`
   distinto, datos propios y URL temporal propia.
3. Intentar recuperar un artefacto con una clave inválida; debe fallar sin revelar su existencia.

### 5. Rendimiento y limpieza

1. Ejecutar 20 imágenes de referencia en el hardware documentado y registrar tiempos totales,
   validación, inferencia y anotación.
2. Confirmar que al menos el 95% termina en cinco segundos o menos.
3. Esperar el TTL configurado y confirmar que la URL temporal responde `410` o `404` según la
   política de limpieza, sin dejar la imagen accesible en el directorio temporal.

## Resultado esperado

La primera iteración queda validada cuando los escenarios anteriores pasan, las pruebas automáticas
se ejecutan sin fallos y se conserva la evidencia de versión de modelo, configuración no secreta,
hardware y métricas obtenidas.

## Evidencia de implementación (2026-10-21)

- Se verificó compilación sintáctica de `app/` y `tests/` con Python 3.12.
- Pasaron 6 pruebas unitarias síncronas: anotación, mapeo de detecciones, fallo de inferencia,
  rechazo sin artefacto, vencimiento y cierre del almacén temporal.
- Se comprobó estáticamente que el OpenAPI generado publica `ApiKeyAuth`,
  `/api/v1/detections/images` y `/health/live`.
- La ejecución de la suite HTTP completa queda pendiente de ejecutarse en un terminal local normal:
  el entorno aislado usado para esta evidencia bloquea `asyncio` antes de arrancar el ciclo de vida
  de FastAPI. No se han afirmado resultados de integración ni de rendimiento real.
- Para cerrar la validación, configurar los pesos aprobados, una clave de prueba y 20 imágenes de
  referencia; después ejecutar `uv run pytest --basetemp .pytest-tmp` y registrar hardware,
  dispositivo y percentil 95 de latencia.
