# Auditoría y cobertura de la primera iteración

**Proyecto**: Sistema de detección de actores viales  
**Funcionalidad auditada**: detección vial en una imagen  
**Fecha de cierre de evidencia**: 2026-11-12
**Fuentes revisadas**: constitución, `spec.md`, `plan.md`, `tasks.md`, `quickstart.md`, contrato OpenAPI, código, pruebas y resultados generados.

## Dictamen ejecutivo

**Estado: validada condicionalmente.** La iteración está implementada, sus pruebas automatizadas pasan y el modelo configurado fue cargado en una comprobación local. Queda una única validación representativa: ejecutar el benchmark con 20 imágenes viales autorizadas y el modelo aprobado para certificar SC-001. La medición con detector falso no se usa para afirmar el rendimiento del modelo.

## Resultados verificables

| Medida | Resultado |
|---|---:|
| Suite automatizada | 29/29 pruebas aprobadas |
| Cobertura global de líneas | 90% |
| Cobertura XML | `.runtime/audit/coverage.xml` |
| Advertencias | 1 deprecación externa de Starlette; sin fallos |
| Benchmark de infraestructura | 20 solicitudes, p95 de 12.32 ms |
| Informe de benchmark | `.runtime/benchmarks/reference-images.json` |
| Comprobación con modelo configurado | `/health/ready` = 200; inferencia de humo = 200 en 744 ms |

El benchmark usó `fake-yolov10s.pt`, CPU y una imagen JPEG sintética de 40×40; es evidencia de la infraestructura y del registro de métricas, no de precisión ni de rendimiento vial real. La inferencia de humo usó el modelo configurado, pero la imagen gris no contiene actores viales y devolvió cero detecciones, como correspondía.

## Trazabilidad de requisitos funcionales

| Requisito | Estado | Evidencia |
|---|---|---|
| FR-001: carga autorizada | Verificado | Pruebas de autenticación y análisis HTTP. |
| FR-002: validación previa | Verificado | Pruebas de MIME, extensión, corrupción, bytes y píxeles. |
| FR-003: modelo aprobado | Verificado operativamente | Carga satisfactoria y solicitud de humo con los pesos configurados. |
| FR-004: clase, confianza y caja | Verificado | Pruebas de mapeo y normalización de cajas. |
| FR-005: visualización anotada | Verificado | Pruebas de anotación, etiqueta y recuperación del JPEG. |
| FR-006: errores seguros | Verificado | Pruebas de respuestas públicas y rechazo estructurado. |
| FR-007: contrato estable | Verificado | Contrato OpenAPI y prueba de consumidor. |
| FR-008: trazabilidad operativa | Verificado | Logs seguros, estados y tiempos por solicitud. |
| FR-009: eliminación temporal | Verificado | Pruebas de vencimiento, limpieza y cierre. |
| FR-010: solicitudes consecutivas | Verificado | Pruebas de identificadores aislados y 20 solicitudes de referencia. |

## Criterios de éxito

| Criterio | Estado | Evidencia o condición |
|---|---|---|
| SC-001: 95% de 20 imágenes ≤5 s | Pendiente | Se requieren 20 imágenes viales autorizadas y medición con el modelo aprobado. |
| SC-002: rechazos seguros | Verificado | Casos no permitidos, corruptos y excesivos aprobados. |
| SC-003: detección y anotación | Verificado | Respuesta estructurada, cajas, etiquetas y JPEG anotado probados. |
| SC-004: cliente consume 20 resultados | Verificado | Prueba de cliente basada solo en campos públicos y contrato. |
| SC-005: 20 solicitudes aisladas | Verificado | Prueba de rendimiento con 20 solicitudes y pruebas de identificadores únicos. |

## Hallazgos de convergencia

| Hallazgo | Evidencia de cierre |
|---|---|
| Rechazos sin log estructurado | `test_rejected_upload_creates_a_safe_structured_log` aprobado. |
| Extensión de archivo no validada | Pruebas de JPEG/PNG y extensión discordante aprobadas. |
| Ruta OpenAPI inconsistente | Contrato y ruta `{requestId}` verificados. |
| Cajas fuera de límites | Prueba de normalización aprobada. |
| Ciclo de vida incompleto | Estados, tiempos y código público cubiertos por pruebas. |
| Etiqueta de anotación no verificada | Prueba de caja, clase y confianza aprobada. |
| Métricas no persistidas | Informe JSON no secreto generado con tiempos, p95, modelo, dispositivo y hardware. |

## Estado de tareas

Se completaron **53 de 54 tareas**. Las tareas T027, T034, T041, T047, T048, T049 y T054 se cerraron con la ejecución de esta auditoría.

La única tarea abierta es **T046**, porque exige ejecutar *todos* los escenarios del quickstart; falta exclusivamente su escenario de rendimiento representativo con 20 imágenes viales reales.

## Riesgos y cierre pendiente

- No se han proporcionado 20 imágenes viales autorizadas de referencia para certificar SC-001.
- La evidencia de rendimiento sintética no sustituye una medición con GPU/CPU objetivo, modelo aprobado y datos representativos.
- Al recibir ese conjunto de imágenes, ejecutar el benchmark real, conservar su informe no secreto, registrar el p95 y marcar T046 como completada si cumple la meta.

## Comando reproducible

```powershell
uv run pytest --basetemp .pytest-tmp-cov --cov=app --cov-report=term-missing --cov-report=xml:.runtime/audit/coverage.xml
```

## Conclusión

La primera iteración es funcional, está cubierta por pruebas automatizadas y es apta para demostración técnica. Su cierre definitivo depende solo de una medición de rendimiento real y representativa, documentada conforme a SC-001.
