# Auditoría de implementación — 002-procesamiento-video-vial

**Fecha:** 2026-11-12  
**Estado:** implementación verificable con video sintético; pendiente la evidencia de rendimiento con el conjunto vial autorizado.

## Evidencia ejecutada

| Evidencia | Resultado |
|---|---:|
| Compilación de `app` y `tests` | Exitosa |
| `uv run pytest --basetemp .pytest-tmp-video-002-final --cov=app --cov-report=term -q` | **53 passed** |
| Cobertura global | **88%** |
| FFmpeg/ffprobe instalados | FFmpeg 9.0.2 / ffprobe 9.0.2; disponibles al agregar su `bin` al `PATH` del proceso. |
| E2E controlado | MP4/H.264 sintético: carga 202, trabajo completado, detecciones y salida anotada. |

## Trazabilidad honesta

| Área | Estado | Evidencia / límite |
|---|---|---|
| Carga autenticada antes de multipart | Implementada y probada | Middleware de `app/api/upload_auth.py`; prueba de rechazo 401. |
| Límite de tamaño y validación MP4/H.264 | Implementada y probada | `VideoValidator`, `FFprobeAdapter` y pruebas unitarias. |
| Cola y estados de trabajo | Implementada y probada | SQLite, UUID, transiciones terminales y recuperación de `processing`. |
| Consulta, cancelación y aislamiento por propietario | Implementada y probada parcialmente | `API_KEYS` admite principales; falta ensayo de carga concurrente de 20 trabajos. |
| Procesamiento, IDs persistentes y salida anotada | Implementado | Trabajador único, detector reutilizado, adaptador ByteTrack para YOLO real y fallback probado. |
| MP4/H.264 anotado | Implementado y probado | Transcodificación FFmpeg 9.0.2 y descarga protegida en E2E controlado. |
| Rendimiento (20 videos, p95) | Pendiente | Falta el conjunto vial autorizado y su ejecución documentada. |
| E2E, contrato y seguridad | Implementado con alcance académico | 51 pruebas, contrato, E2E controlado y [revisión de seguridad](security-review.md). |

## Hallazgos y acciones pendientes

1. Ejecutar el benchmark con 20 videos viales autorizados antes de declarar SC-003 y SC-005 conformes.
2. Validar ByteTrack con los pesos YOLOv10s aprobados, no solo con el detector determinista de prueba.
3. Reiniciar Codex o PowerShell para que el `PATH` actualizado de FFmpeg sea heredado automáticamente.

## Requisitos y criterios

| Ítem | Estado | Evidencia |
|---|---|---|
| FR-001 a FR-006 | Conforme | Rutas, validación, cola y E2E controlado. |
| FR-007 | Parcial | Adaptador ByteTrack implementado; falta validación con modelo aprobado. |
| FR-008 a FR-014 | Conforme | Resumen, artefacto temporal, cancelación, límites, logs, TTL y contrato. |
| SC-001, SC-002, SC-004, SC-006 | Conforme en conjunto controlado | Pruebas unitarias, integración y E2E. |
| SC-003, SC-005 | Pendiente | Requieren 20 videos viales de referencia y medición reproducible. |
