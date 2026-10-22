# Implementation Plan: Detección vial en imagen

**Branch**: `001-deteccion-imagen-vial` | **Date**: 2026-10-21 | **Spec**: [spec.md](spec.md)

## Summary

Construir un microservicio de detección para una imagen por solicitud. Una interfaz cliente
autorizada enviará una imagen, recibirá las detecciones normalizadas (clase, confianza y caja) y una
URL temporal para recuperar la imagen anotada. Se reutilizará el comportamiento del detector
YOLOv10s evaluado en `Vehicle_Detection_System`, aislándolo detrás de un contrato de inferencia y
eliminando de esta iteración los módulos de atributos, placas, video y cámara.

## Technical Context

**Language/Version**: Python 3.12.

**Primary Dependencies**: FastAPI, Uvicorn, Pydantic, python-multipart, Ultralytics compatible con
los pesos YOLOv10s aprobados, OpenCV, Pillow, pytest y httpx/TestClient.

**Storage**: Sin base de datos ni historial persistente. Directorio temporal privado, configurable y
con limpieza por tiempo de vida para la imagen anotada.

**Testing**: pytest; pruebas unitarias con dobles del adaptador de inferencia, de integración para
las rutas HTTP y contractuales contra `contracts/openapi.yaml`; imágenes de prueba controladas.

**Target Platform**: Desarrollo en Windows 11 con Python 3.12; despliegue objetivo en Linux x86_64
con GPU NVIDIA/CUDA cuando esté disponible. El dispositivo se define por configuración y se registra
en las mediciones.

**Project Type**: Microservicio web de una sola aplicación.

**Performance Goals**: Al menos el 95% de 20 imágenes de referencia se completa en cinco segundos o
menos en el hardware documentado; el modelo se carga una vez durante el arranque del proceso y no se
reinicializa para cada solicitud.

**Constraints**: Una imagen por solicitud; formatos JPEG y PNG; tamaño máximo inicial configurable de
10 MiB; máximo inicial de 16 megapíxeles tras decodificación; resultados e imágenes temporales con
TTL inicial de 15 minutos; autenticación por clave de API configurada fuera del código; sin placas,
atributos, video, cámara, historial ni interfaz web de producción.

**Scale/Scope**: Primera iteración académica con un consumidor de interfaz de prueba, 20 imágenes de
referencia y procesamiento síncrono de una imagen. La concurrencia se limita por configuración para
evitar saturar la memoria de GPU.

## Constitution Check

*GATE: PASS before Phase 0 research. Re-checked after Phase 1 design: PASS.*

| Principio | Diseño que asegura el cumplimiento |
|-----------|------------------------------------|
| Arquitectura modular y contratos explícitos | `api`, `services`, `adapters`, `schemas` y `core` se separan; la ruta depende de un servicio y de un protocolo de detector, no de Ultralytics ni del sistema de archivos. |
| Validación, errores y trazabilidad | Se valida MIME declarado, tamaño, firma/decodificación y píxeles antes de inferir. Los errores usan un esquema común sin rutas ni secretos; cada solicitud lleva un identificador y métricas. |
| Seguridad y protección de datos | Las rutas de análisis y de imagen anotada requieren clave de API. Las cargas usan nombres aleatorios, permanecen en un directorio privado y se eliminan por TTL o al fallar. La API no procesa placas en esta iteración. |
| Pruebas y calidad del modelo | El adaptador conserva como línea base los pesos YOLOv10s evaluados; pruebas unitarias, de integración, contrato y rendimiento cubren los requisitos. Un cambio de pesos o umbral requiere evidencia comparativa. |
| Rendimiento y recursos | El modelo se inicializa durante el ciclo de vida de la aplicación; se limita tamaño, megapíxeles y concurrencia. Se registran duración de validación, inferencia y anotación. |

No hay violaciones que requieran seguimiento de complejidad.

## Project Structure

### Documentation (this feature)

```text
specs/001-deteccion-imagen-vial/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── openapi.yaml
├── checklists/
│   └── requirements.md
└── tasks.md                    # Created by $speckit-tasks
```

### Source Code (repository root)

```text
app/
├── api/
│   ├── dependencies.py         # Authentication and request dependencies
│   ├── error_handlers.py       # Safe, shared HTTP errors
│   └── routes/
│       ├── detections.py       # Upload and annotated-image routes
│       └── health.py           # Liveness and readiness routes
├── core/
│   ├── config.py               # Typed environment configuration
│   ├── logging.py              # Structured logging setup
│   └── lifespan.py             # One-time model and temp-store lifecycle
├── domain/
│   ├── models.py               # Internal request, detection and artifact entities
│   └── schemas.py              # Public request/response schemas
├── services/
│   ├── image_validation.py     # Type, size, decode and dimension validation
│   ├── detection_service.py    # Orchestrates validation, inference and response
│   ├── annotation_service.py   # Draws class, confidence and bounding boxes
│   └── temporary_artifacts.py  # Private TTL storage and cleanup
├── adapters/
│   └── yolov10_detector.py     # YOLOv10s inference adapter behind a protocol
└── main.py                     # Application factory and route registration

tests/
├── contract/
│   └── test_openapi_contract.py
├── integration/
│   ├── test_detection_routes.py
│   └── test_artifact_access.py
├── performance/
│   └── test_reference_images.py
└── unit/
    ├── test_image_validation.py
    ├── test_detection_service.py
    └── test_temporary_artifacts.py
```

**Structure Decision**: Una aplicación única conserva el alcance académico y evita acoplar la futura
interfaz web al servicio. Las dependencias de infraestructura quedan en adaptadores y core; el
dominio y los servicios no importan módulos de ruta ni acceden directamente al modelo.

## Complexity Tracking

No se requieren excepciones a la constitución.
