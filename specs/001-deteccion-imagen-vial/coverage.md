# Auditoría y cobertura de la primera iteración

**Proyecto**: Sistema de detección de actores viales  
**Funcionalidad auditada**: detección vial en una imagen  
**Fecha**: 2026-10-21  
**Fuentes revisadas**: `spec.md`, `plan.md`, `tasks.md`, `quickstart.md`, contrato OpenAPI, constitución, código y pruebas.

## Dictamen ejecutivo

La primera iteración implementa un microservicio FastAPI que recibe una imagen vial, devuelve detecciones estructuradas y entrega una imagen anotada temporal protegida por clave de API.

**Estado: CONDICIONAL.** La implementación y los artefactos SDD existen, pero la iteración no debe declararse completamente cerrada hasta ejecutar las pruebas HTTP/asíncronas y el benchmark de 20 imágenes con el modelo y hardware reales. Este documento no infiere resultados no ejecutados.

## Evidencia de implementación

| Componente | Evidencia | Estado |
|---|---|---|
| API y ciclo de vida | `app/main.py`, `app/core/lifespan.py` | Implementado |
| Autenticación y errores seguros | `app/api/dependencies.py`, `app/api/error_handlers.py` | Implementado |
| Validación de carga | `app/services/image_validation.py` | Implementado |
| Adaptador YOLOv10s | `app/adapters/yolov10_detector.py` | Implementado; pesos reales pendientes |
| Detecciones y anotación | `app/services/detection_service.py`, `app/services/annotation_service.py` | Implementado |
| Artefactos temporales | `app/services/temporary_artifacts.py` | Implementado |
| Contrato público | `contracts/openapi.yaml` | Ruta `{requestId}` comprobada |
| Estados y métricas | `AnalysisRequest`, logs y benchmark | Implementado; evidencia real pendiente |

## Trazabilidad de requisitos funcionales

| Requisito | Evidencia | Estado |
|---|---|---|
| FR-001: carga autorizada | Rutas y API key; T011, T025 | Implementado; prueba HTTP pendiente |
| FR-002: validación previa | MIME, extensión, bytes, decodificación y píxeles; T031, T049 | Implementado; prueba asíncrona pendiente |
| FR-003: modelo aprobado | Adaptador y carga única al iniciar; T013, T021 | Implementado; modelo real pendiente |
| FR-004: clase, confianza y caja | Esquemas y límites de caja; T024, T051 | Verificado unitariamente |
| FR-005: visualización anotada | Anotación y URL temporal; T022, T023 | Verificado unitariamente; HTTP pendiente |
| FR-006: errores seguros | Manejadores y códigos públicos; T012, T033 | Implementado; HTTP pendiente |
| FR-007: contrato estable | OpenAPI y prueba contractual; T035, T039, T050 | Verificado estáticamente |
| FR-008: trazabilidad operativa | Logs de éxito, fallo y rechazo; T007, T048 | Implementado; captura HTTP pendiente |
| FR-009: eliminación temporal | TTL, limpieza y cierre; T023, T038, T043 | Verificado unitariamente |
| FR-010: solicitudes consecutivas | Detector compartido y límite de concurrencia; T013, T024 | Implementado; integración pendiente |

## Criterios de éxito

| Criterio | Estado | Evidencia o condición pendiente |
|---|---|---|
| SC-001: 95% de 20 imágenes en ≤5 s | Pendiente | Ejecutar benchmark con modelo, imágenes y hardware reales. |
| SC-002: rechazos seguros | Parcial | Código y pruebas creadas; falta corrida HTTP/asíncrona. |
| SC-003: detecciones y visualización | Parcial | Pruebas unitarias aprobadas; falta flujo HTTP completo. |
| SC-004: cliente consume 20 resultados | Pendiente | Prueba creada, no ejecutada. |
| SC-005: 20 solicitudes aisladas | Pendiente | Prueba creada, no ejecutada. |

## Pruebas y cobertura

Comando ejecutado:

```powershell
uv run pytest --basetemp .pytest-tmp tests/unit/test_annotation_service.py tests/unit/test_detection_service.py tests/unit/test_temporary_artifacts.py tests/contract/test_openapi_contract.py --cov=app --cov-report=term-missing --cov-report=xml:.runtime/audit/coverage-unit.xml
```

| Medida | Resultado | Alcance |
|---|---:|---|
| Pruebas aprobadas | 8/8 | Unitarias síncronas y contrato OpenAPI estático |
| Pruebas recolectadas | 29 | La suite completa se detectó; no equivale a una ejecución satisfactoria |
| Cobertura de líneas | 66% | Solo las 8 pruebas ejecutadas, no cobertura global certificada |
| Archivo de evidencia | `.runtime/audit/coverage-unit.xml` | Generado localmente y sin secretos |

Las pruebas HTTP, multipart, integración y rendimiento no se ejecutaron en este entorno porque `asyncio` queda bloqueado por el aislamiento de ejecución. Deben correr en un terminal local normal.

## Hallazgos de convergencia

| Hallazgo | Acción aplicada | Estado |
|---|---|---|
| Rechazos sin log estructurado | Se agregó estado `rejected` y log seguro. | Código listo; T048 pendiente de prueba HTTP |
| Extensión no validada | Se aceptan `.jpg`, `.jpeg` y `.png`. | Código listo; T049 pendiente de prueba asíncrona |
| Ruta OpenAPI inconsistente | Se alineó `{requestId}` y se fortaleció el contrato. | Cerrado: T050 |
| Cajas fuera de límites | Se normalizan al tamaño de la imagen. | Cerrado: T051 |
| Ciclo de vida incompleto | Se añadieron fecha, tiempos, estado y código de error. | Cerrado: T052 |
| Etiqueta no verificada | La prueba comprueba clase y confianza. | Cerrado: T053 |
| Métricas no persistidas | Benchmark prepara informe JSON no secreto. | Código listo; T054 pendiente de ejecución |

## Estado de tareas

Hay **46 tareas completadas** y **8 pendientes**.

| Tareas pendientes | Condición de cierre |
|---|---|
| T027, T034, T041 | Ejecutar las pruebas de US1, US2 y US3. |
| T046 | Ejecutar suite total y escenarios del quickstart. |
| T047 | Revisar FR-001 a FR-010 y SC-001 a SC-005 con evidencia final. |
| T048, T049, T054 | Ejecutar y aprobar pruebas HTTP/asíncronas y benchmark. |

## Riesgos y limitaciones

- Aún no hay evidencia de carga y detección con `yolov10s_best.pt` en el equipo objetivo.
- El 66% no es cobertura final porque excluye rutas HTTP y pruebas asíncronas.
- SC-001 requiere registrar imágenes autorizadas, dispositivo, hardware, versión del modelo y percentil 95.
- La constitución contempla video como regla general; esta especificación excluye video y cámara en la primera iteración. Debe cubrirse al ampliar el alcance.

## Procedimiento de cierre

En PowerShell local, desde la raíz del proyecto:

```powershell
uv run pytest --basetemp .pytest-tmp --cov=app --cov-report=term-missing --cov-report=html
```

Después, configurar una `.env` privada con `MODEL_WEIGHTS_PATH`, `API_KEY` e `INFERENCE_DEVICE`; ejecutar el benchmark con 20 imágenes de referencia y conservar `.runtime/benchmarks/reference-images.json` como evidencia. Si los resultados son satisfactorios, marcar T027, T034, T041, T046, T048, T049 y T054; luego completar T047 y actualizar este documento con la cobertura global real.

## Conclusión

La iteración cuenta con documentación SDD, implementación trazable y evidencia parcial verificable. Está lista para validación integrada local, pero no debe declararse cerrada hasta completar las tareas pendientes y registrar la cobertura final.
