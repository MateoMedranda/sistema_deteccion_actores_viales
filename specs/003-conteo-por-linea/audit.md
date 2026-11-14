# Auditoría de implementación: Conteo de actores por línea

**Fecha**: 2026-11-13  
**Rama**: `feature/003-conteo-por-linea`

## Evidencia implementada

| Área | Evidencia |
|---|---|
| Línea normalizada y cruces | `app/services/line_counting.py`; pruebas de validación, direcciones y trayectorias controladas. |
| Persistencia temporal | `app/services/count_job_store.py`; SQLite con unicidad por `count_job_id`/`track_id`, TTL y aislamiento por propietario. |
| API protegida | `app/api/routes/count_jobs.py`; API key heredada, creación, estado, eventos y MP4 anotado. |
| Sin reinferencia | `app/services/count_processing.py` consume únicamente `FrameDetection` persistida. |
| Evidencia visual | `app/services/count_annotation_service.py` superpone línea, sentidos y contadores sobre el video temporal existente. |

## Pruebas ejecutadas

- Correctas: compilación de `app` y `tests` mediante `python -m compileall -q app tests`.
- Correctas: suite completa `python -m pytest --basetemp .pytest-tmp --cov=app --cov-report=term-missing -q`: todas las pruebas ejecutables pasaron; tres se omitieron por no disponer de FFmpeg para fabricar MP4 de integración.
- Cobertura global observada: 78%. La geometría de línea, el almacén de conteo, el procesador sin detector, la anotación, el contrato y el control de acceso tienen pruebas específicas.

## Cobertura de requisitos

- FR-001 a FR-003: creación autenticada, línea normalizada y validación previa.
- FR-004 a FR-007a: cruce por centro, deduplicación, dirección, eventos y progreso incremental.
- FR-008 a FR-013: MP4 temporal, aislamiento, reutilización de detecciones, TTL, logs y OpenAPI.

## Limitaciones y seguimiento

- Ejecutar la suite completa con FFmpeg disponible y registrar sus resultados antes de una entrega de producción.
- El conjunto de diez trayectorias controladas valida la geometría; debe complementarse con diez videos viales autorizados para validar la calidad del rastreador en condiciones reales.
