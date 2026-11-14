# Implementation Plan: Extracción de características y placas

**Branch**: `004-extraccion-caracteristicas-y-placas` | **Date**: 2026-11-14 | **Spec**: [spec.md](spec.md)

## Summary

Ampliar el microservicio existente para crear trabajos temporales de enriquecimiento sobre detecciones viales ya terminadas. Cada trabajo toma recortes válidos de vehículos desde una imagen o video de su propietario, ejecuta en ramas independientes la extracción de atributos y la localización/lectura protegida de placas, y devuelve un resultado por detección de imagen o un resultado consolidado por `track_id` en video. La lectura de placa usa el recorte original primero; solo ante baja confianza aplica rectificación y mejora conservadora para un único reintento. Las fuentes, recortes y resultados sensibles se eliminan a más tardar al vencer la fuente de origen.

## Technical Context

**Language/Version**: Python 3.12.

**Primary Dependencies**: FastAPI 0.115, Pydantic Settings, SQLite estándar, OpenCV, Pillow, Ultralytics; se añadirán dependencias explícitas y compatibles para PaddleOCR/PaddlePaddle y el cargador del checkpoint EfficientNet-B1 aprobado. Pytest, httpx/TestClient y pytest-cov para pruebas.

**Storage**: SQLite temporal para trabajos y resultados de enriquecimiento; un registro temporal y privado de fuentes de imagen; directorios privados de entrada, recortes y variantes de placa con nombres aleatorios. Los videos reutilizan su trabajo y detecciones existentes, pero conservarán temporalmente la fuente original hasta su vencimiento.

**Testing**: Unitarias para recortes, calidad, reintento único, consenso y TTL; integración de autorización, estados, errores, aislamiento y limpieza; contratos OpenAPI; E2E con imágenes y videos controlados; smoke tests separados para los pesos aprobados. Las pruebas ordinarias usan adaptadores falsos y no requieren pesos reales.

**Target Platform**: Desarrollo en Windows 11; despliegue Linux x86_64. El dispositivo de inferencia se configura externamente y puede ser CPU o GPU compatible con las dependencias aprobadas.

**Project Type**: Microservicio web FastAPI de una aplicación, sin frontend.

**Performance Goals**: Aceptar el trabajo en máximo 2 segundos; no reejecutar el detector vial base; cargar cada modelo una sola vez al inicio; registrar p50/p95 de cada rama, tiempo por vehículo/track, memoria y errores. La calidad se verifica con al menos 20 recortes y 10 tracks controlados según `spec.md`.

**Constraints**: API key y aislamiento por propietario obligatorios; máximo un trabajo consolidado por `track_id`; resultados de placa solo para su propietario; TTL = mínimo entre fuente y límite de enriquecimiento; mejora no generativa, un solo reintento de OCR, sin autocompletar caracteres; concurrencia y número de fotogramas de evidencia configurables y acotados.

**Scale/Scope**: Hereda los límites de imagen y video de las iteraciones 001/002 (hasta 120 s, 3600 cuadros, 1080p y 30 fps para video). Un trabajador de enriquecimiento por defecto y ramas internas acotadas. No incluye frontend, cámara, historial, exportación, reentrenamiento ni reconocimiento facial.

## Constitution Check

*GATE: PASS before Phase 0 research. Re-checked after Phase 1 design: PASS.*

| Principio | Diseño que asegura el cumplimiento |
|---|---|
| I. Arquitectura modular y contratos explícitos | Las rutas usan `EnrichmentJobService`; adaptadores tipados aíslan atributos, localizador de placa, OCR y preprocesamiento. Ninguna ruta accede a pesos ni archivos directamente. |
| II. Validación, errores y trazabilidad | Se validan propietario, estado y TTL de fuente, elegibilidad del vehículo, límites de recorte, umbrales y estados. Los errores públicos no muestran rutas, pesos, textos de placa ni excepciones. |
| III. Seguridad y protección de datos | La fuente, recortes, texto y evidencia de placa se aíslan por `owner_key_id`, viven solo en almacenamiento privado temporal y se excluyen de logs, métricas y URLs públicas. |
| IV. Pruebas verificables y calidad del modelo | Hay fixtures controladas, mocks de modelos, smoke tests con pesos, métricas por atributo/localización/OCR y comparación entre OCR original, reintento y consenso. Se exigirá manifiesto reproducible del modelo. |
| V. Rendimiento y recursos | Los modelos se inicializan una vez; la cola y las ramas tienen límites configurables; se seleccionan fotogramas de evidencia por track para evitar inferencias redundantes y se miden latencia/memoria/errores. |

## Project Structure

### Documentation

```text
specs/004-extraccion-caracteristicas-y-placas/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── openapi.yaml
└── tasks.md                 # generado después por speckit-tasks
```

### Source Code

```text
app/
├── adapters/
│   ├── attribute_extractor_protocol.py
│   ├── efficientnet_attribute_extractor.py
│   ├── plate_localizer_protocol.py
│   ├── yolov8_plate_localizer.py
│   ├── plate_reader_protocol.py
│   └── paddle_plate_reader.py
├── api/routes/
│   └── enrichment_jobs.py
├── core/
│   ├── config.py
│   └── lifespan.py
├── domain/
│   ├── models.py
│   └── schemas.py
└── services/
    ├── image_detection_store.py
    ├── source_artifacts.py
    ├── enrichment_job_store.py
    ├── enrichment_job_service.py
    ├── enrichment_processing.py
    ├── enrichment_worker.py
    ├── vehicle_cropping.py
    ├── plate_quality.py
    └── plate_consensus.py

tests/
├── unit/
│   ├── test_vehicle_cropping.py
│   ├── test_plate_quality.py
│   ├── test_plate_consensus.py
│   └── test_enrichment_job_store.py
├── integration/
│   ├── test_enrichment_job_routes.py
│   ├── test_enrichment_source_access.py
│   └── test_enrichment_cleanup.py
├── contract/
│   └── test_enrichment_contract.py
├── e2e/
│   └── test_enrichment_regression.py
└── performance/
    └── test_enrichment_reference_benchmark.py
```

**Structure Decision**: Se amplía la única aplicación FastAPI. La iteración reutiliza autenticación, patrón de trabajos temporales, SQLite, detecciones por fotograma y ciclo de vida de 001–003; añade módulos de enriquecimiento separados para no acoplar rutas, modelos ni almacenamiento de fuentes.

## Complexity Tracking

No se requieren excepciones a la constitución. La retención temporal de la fuente original es necesaria para formar recortes sin reinferencia y está limitada por el TTL, propietario y limpieza obligatoria.
