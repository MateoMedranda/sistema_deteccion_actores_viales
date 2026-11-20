# Auditoría de implementación: Iteración 004

**Fecha:** 2026-11-14
**Alcance auditado:** enriquecimiento temporal de detecciones existentes con atributos visuales y análisis protegido de placas.

## Evidencia implementada

- Se agregó `POST /api/v1/enrichment-jobs`, consulta, cancelación y resultados paginados, todos protegidos por `X-API-Key`.
- Una detección de imagen conserva de forma privada el original y sus cajas durante el TTL; tanto la imagen anotada como las fuentes de enriquecimiento verifican propietario.
- Un video terminado conserva su entrada privada hasta el TTL para extraer recortes sin volver a ejecutar el detector vial.
- La cola temporal de enriquecimiento usa SQLite y recupera trabajos `processing` vigentes como `queued` al reiniciar.
- EfficientNet-B1 utiliza un manifiesto verificable con las etiquetas VeRi observadas en el proyecto de investigación. El OCR hace una primera lectura y como máximo un reintento no generativo; no aplica correcciones por expresión regular ni inventa caracteres.

## Pruebas ejecutadas

| Comando | Resultado |
|---|---|
| `uv run pytest tests/unit/test_enrichment_core.py tests/unit/test_enrichment_job_store.py tests/unit/test_track_consolidation.py tests/unit/test_plate_quality.py tests/integration/test_enrichment_job_routes.py --basetemp .pytest-tmp-004-check -q` | 7 aprobadas |
| `uv run pytest --basetemp .pytest-tmp-004-final --cov=app --cov-report=term-missing -q` | 84% de cobertura total; 1 fallo heredado de conteo por línea |

El único fallo de la suite completa fue `tests/integration/test_count_job_routes.py::test_count_job_reports_one_directional_event`: el trabajo de conteo termina pero no registra el evento esperado. No pertenece al flujo añadido en esta iteración y queda pendiente de corrección/regresión de la iteración 003.

## Limitaciones y trabajo pendiente real

1. El smoke con modelos reales no se completó: el checkpoint EfficientNet se puede abrir mediante `weights_only=True`, pero importar PaddleOCR alcanza `torch/lib/shm.dll` y falla con `WinError 127`. Se fijó PaddleOCR 2.x, compatible con el adaptador aprobado, pero debe repararse la instalación nativa de PyTorch/Microsoft Visual C++ antes de ejecutar los smoke/E2E con los pesos autorizados.
2. Faltan la evaluación anotada de 20 recortes y 10 tracks, sus métricas de F1/AP/CER/tasa de lectura falsa y el benchmark p50/p95.
3. La consolidación actual selecciona la evidencia de mayor confianza por `track_id`; queda pendiente implementar consenso multi-fotograma de placas y la persistencia relacional detallada de candidatos.
4. Faltan las pruebas de contrato completas, limpieza/expiración de variantes, límites de concurrencia por modelo y telemetría p50/p95.

## Decisión de seguridad

No se publican rutas locales, recortes de vehículos/placas, ni textos de OCR que no superen el umbral. Los resultados de placa solo pueden aparecer para el propietario autenticado y con estado `read`.

## Corrección de ejecución con modelos reales — 2026-11-20

- Se reprodujo `plate_processing_failed` en una imagen original proporcionada por el usuario (2124 × 1005). YOLOv8n sí localizaba placas; la excepción ocurría en PaddleOCR: `NotFoundError: OneDnnContext does not have the input Filter`, operador `fused_conv2d`, con Paddle 3.3.1.
- PaddleOCR 2.x fuerza optimización del grafo y no desactiva explícitamente oneDNN cuando `enable_mkldnn=False`. El adaptador ahora desactiva oneDNN y las optimizaciones incompatibles en los tres predictores durante su construcción; el hook se restaura al terminar. Carga Torch antes de Paddle en Windows y serializa el acceso al predictor OCR.
- El umbral de placas se pasa directamente a YOLO. Antes, reducirlo por debajo de 0.25 no podía recuperar cajas ya filtradas por el umbral interno de YOLO; bajar solamente el filtro posterior no resolvía este problema.
- Si la lectura falla, se conserva la caja y confianza del localizador. El registro identifica etapa y tipo de excepción sin publicar mensajes internos ni caracteres de placas.
- El reintento conserva la primera lectura sobre el original. Se corrigió la normalización del ángulo que podía rotar una placa horizontal 90 grados y se evita recortar los extremos al rectificar. La mejora usa ampliación acotada y contraste CLAHE, sin generar caracteres.
- Se verificó que arquitectura, etiquetas, entrada 240 × 240 y normalización del manifiesto EfficientNet coinciden con `core/attributes_model.py` del repositorio de investigación. La localización usa el mismo checkpoint ALPR y recortes BGR de vehículos que su `core/alpr_model.py`.

### Resultado observado

Prueba con los pesos reales configurados y `ITB3BGJW45C27PEIPUCRDPFLYU.jpg`, incluyendo las dos ramas ejecutadas en hilos por `EnrichmentProcessor`:

| Medida | Resultado |
|---|---:|
| Actores detectados | 21 |
| Atributos completados | 21 |
| Placas localizadas | 11 |
| Localizadas con lectura insuficiente (`unreadable`) | 11 |
| Placa no localizada (`not_detected`) | 10 |
| Fallos de procesamiento | 0 |
| Textos aceptados (`read`) | 0 |

También se probó CLAHE como en el repositorio original sobre los mismos recortes: no produjo texto en esas 11 placas en el entorno actual. Las variantes experimentales de ampliación y reconocimiento directo no alcanzaron confianza 0.80; no se incorporó una relajación del umbral de aceptación ni se inventaron caracteres. Esto demuestra ejecución estable, no precisión OCR ni equivalencia con resultados históricos. Las placas son pequeñas (varios recortes de unos 10–13 píxeles de alto); sigue siendo necesaria una evaluación con transcripción real y comparación del entorno original para establecer CER y lecturas falsas. No se modificaron pesos ni el repositorio de investigación.

El `requirements.txt` del repositorio de investigación declara PaddleOCR 2.9.1 y PaddlePaddle 2.6.2; este backend ejecuta PaddlePaddle 3.3.1. La comparación de código/preprocesamiento se hizo en el entorno actual, no en una reproducción instalada del entorno 2.6.2. Esa diferencia impide atribuir todos los cambios de lectura exclusivamente a resolución o umbrales.

Las pruebas de regresión cubren configuración del predictor, umbral real de YOLO, conservación de cajas ante errores, registros seguros, lectura observada y rectificación sin rotaciones espurias. La fixture HTTP ahora ignora el `.env` personal y usa almacenamiento de enriquecimiento aislado para no consumir modelos ni trabajos del usuario.

Verificación final: `.venv/Scripts/python.exe -m pytest` — **101 aprobadas**, dos avisos de dependencias, sin fallos. `git diff --check` sin errores.
