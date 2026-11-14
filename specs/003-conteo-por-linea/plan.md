# Implementation Plan: Conteo de actores por línea

**Branch**: 003-conteo-por-linea | **Date**: 2026-11-13 | **Spec**: [spec.md](spec.md)

## Summary

Añadir conteo direccional sobre un video vial terminado y vigente. Un usuario autorizado crea un trabajo temporal con una línea orientada de dos puntos normalizados. El trabajo recorre las detecciones ya almacenadas, cuenta una sola vez cada track_id cuyo centro cambia de lado, publica avance, eventos y totales acumulados, y genera un video temporal con la línea y contadores. No se reejecuta el modelo ni se incluye frontend.

## Technical Context

**Language/Version**: Python 3.12.

**Primary Dependencies**: FastAPI, Pydantic Settings, OpenCV, SQLite estándar, pytest, httpx/TestClient y dependencias de video existentes.

**Storage**: SQLite temporal existente, ampliado con configuraciones, trabajos, eventos y agregados de conteo; directorio privado temporal para el video anotado. Los datos no sobreviven al vencimiento del video origen.

**Testing**: Pruebas unitarias de geometría y deduplicación; integración HTTP de autorización, progreso, aislamiento, vencimiento y resultados; contrato OpenAPI y E2E con al menos 10 videos controlados de cruce conocido.

**Target Platform**: Windows 11 para desarrollo y Linux x86_64 para despliegue, con los requisitos de video de la iteración 002.

**Project Type**: Microservicio web de una sola aplicación, sin frontend.

**Performance Goals**: Confirmar el trabajo en máximo 2 segundos; no invocar nuevamente el modelo; completar 10 videos controlados sin conteos duplicados ni cruces falsos.

**Constraints**: Una línea por configuración; puntos normalizados entre 0 y 1; un evento máximo por track_id y configuración; sentidos A_to_B/B_to_A; videos terminados y no vencidos; resultados temporales aislados por propietario.

**Scale/Scope**: Un trabajador de conteo configurable por defecto; videos de hasta 120 segundos y 3600 fotogramas heredados de 002; sin cámara, múltiples líneas, zonas, historial, placas, OCR ni frontend.

## Constitution Check

*GATE: PASS before Phase 0 research. Re-checked after Phase 1 design: PASS.*

| Principio | Diseño que asegura el cumplimiento |
|---|---|
| I. Arquitectura modular y contratos explícitos | Rutas dependen de un servicio de conteo; geometría, almacén, renderizado y trabajador permanecen separados y tipados. |
| II. Validación, errores y trazabilidad | Se validan propietario, estado/vencimiento del video, finitud/rango de puntos y longitud de línea; errores y logs conservan formas seguras. |
| III. Seguridad y protección de datos | Toda consulta filtra por principal; eventos y video de conteo heredan TTL y aislamiento del trabajo origen. |
| IV. Pruebas verificables y calidad del modelo | El conteo se prueba con trayectorias controladas y regresión de video sin cambiar pesos, umbral ni detección. |
| V. Rendimiento y recursos | No hay inferencia nueva; se registran duración, fotogramas, eventos, memoria y errores por trabajo. |

## Project Structure

### Documentation

    specs/003-conteo-por-linea/
    ├── plan.md
    ├── research.md
    ├── data-model.md
    ├── quickstart.md
    ├── contracts/openapi.yaml
    └── tasks.md

### Source Code

    app/
    ├── api/routes/count_jobs.py
    ├── core/config.py
    ├── core/lifespan.py
    ├── domain/models.py
    ├── domain/schemas.py
    ├── services/line_counting.py
    ├── services/count_job_store.py
    ├── services/count_processing.py
    ├── services/count_worker.py
    └── main.py

    tests/
    ├── contract/test_count_jobs_contract.py
    ├── integration/test_count_job_routes.py
    ├── integration/test_count_artifact_access.py
    ├── e2e/test_line_counting_regression.py
    └── unit/test_line_counting.py

**Structure Decision**: Se amplía la aplicación FastAPI existente. La iteración reutiliza cola temporal, autorización, detecciones por fotograma y artefactos de 002; añade un flujo de conteo independiente para preservar la separación entre detección y analítica.

## Complexity Tracking

No se requieren excepciones a la constitución.

