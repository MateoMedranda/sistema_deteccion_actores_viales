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
| `uv run pytest tests/unit/test_enrichment_core.py tests/integration/test_enrichment_job_routes.py --basetemp .pytest-tmp-004-run-d -q` | 4 aprobadas |
| `uv run pytest --basetemp .pytest-tmp-004-run-b -q` | 83 aprobadas, 1 fallo heredado de conteo por línea |

El único fallo de la suite completa fue `tests/integration/test_count_job_routes.py::test_count_job_reports_one_directional_event`: el trabajo de conteo termina pero no registra el evento esperado. No pertenece al flujo añadido en esta iteración y queda pendiente de corrección/regresión de la iteración 003.

## Limitaciones y trabajo pendiente real

1. El smoke con modelos reales no se completó: en este equipo `import torch` falla al cargar `torch/lib/shm.dll` (`WinError 127`). Debe repararse la instalación nativa de PyTorch/Microsoft Visual C++ y ejecutar los smoke/E2E con los pesos autorizados.
2. Faltan la evaluación anotada de 20 recortes y 10 tracks, sus métricas de F1/AP/CER/tasa de lectura falsa y el benchmark p50/p95.
3. La consolidación actual selecciona la evidencia de mayor confianza por `track_id`; queda pendiente implementar consenso multi-fotograma de placas y la persistencia relacional detallada de candidatos.
4. Faltan las pruebas de contrato completas, limpieza/expiración de variantes, límites de concurrencia por modelo y telemetría p50/p95.

## Decisión de seguridad

No se publican rutas locales, recortes de vehículos/placas, ni textos de OCR que no superen el umbral. Los resultados de placa solo pueden aparecer para el propietario autenticado y con estado `read`.
