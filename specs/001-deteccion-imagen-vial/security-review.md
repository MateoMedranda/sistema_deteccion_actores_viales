# Revisión de seguridad de implementación

**Fecha**: 2026-10-21  
**Alcance**: primera iteración de detección de una imagen, conforme a `plan.md`.

| Control del plan | Evidencia de implementación | Resultado |
|------------------|-----------------------------|-----------|
| Clave de API en rutas protegidas | `app/api/dependencies.py` usa `X-API-Key` y `secrets.compare_digest`; las rutas de análisis y del artefacto la requieren. | Conforme |
| No registrar secretos | El formateador solo incluye identificador, estado y duraciones; no incorpora cabeceras, pesos ni bytes de imagen. | Conforme |
| Límites de carga | `app/services/image_validation.py` limita bytes, MIME, formato real, decodificación y píxeles antes de inferencia. | Conforme |
| Almacenamiento temporal privado | `TemporaryArtifactStore` usa nombres aleatorios, TTL, eliminación al cerrar y no expone rutas del sistema de archivos. | Conforme |
| Acceso a artefactos | La recuperación exige clave de API y distingue artefacto inexistente (`404`) de vencido (`410`) sin revelar rutas. | Conforme |
| Exposición de errores | `ApiError` y los manejadores globales devuelven solo `code`, `message` y `request_id`. | Conforme |

## Seguimiento operativo

Antes del despliegue real se debe configurar TLS, un proxy con límite de tamaño y tasa, directorios
privados con permisos del proceso y un gestor de secretos. La evaluación con los pesos reales debe
confirmar que la configuración de GPU elegida no introduce registros adicionales ni rutas sensibles.
