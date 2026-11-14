# Revisión de seguridad — 002-procesamiento-video-vial

**Fecha:** 2026-11-12  
**Resultado:** aprobado para entorno académico local, condicionado a las limitaciones indicadas.

| Control | Evidencia | Estado |
|---|---|---|
| Autorización previa a carga | `app/api/upload_auth.py` valida `X-API-Key` antes de delegar el cuerpo multipart. | Conforme |
| Aislamiento | Cada búsqueda SQLite filtra por `owner_key_id`; credenciales múltiples usan identificadores distintos. | Conforme |
| Archivos temporales | Entrada y salida usan UUID, directorio privado y no exponen rutas del host. | Conforme |
| Vencimiento | Trabajos vencidos registran `410`; las rutas de artefacto se eliminan durante limpieza. | Conforme |
| Errores públicos | `ApiError` retorna código, mensaje estable e ID de solicitud, sin claves ni rutas internas. | Conforme |
| Registros | Se registran IDs, métricas y códigos seguros; no se registra contenido, rutas privadas ni secretos. | Conforme |

## Límites operativos

- Desplegar tras TLS/proxy, con permisos restrictivos sobre `.runtime/`.
- Usar secretos distintos por principal mediante `API_KEYS`; no subir `.env` al repositorio.
- La cola SQLite es local, apropiada para un único proceso. Para escalar horizontalmente se requiere una cola compartida y almacenamiento de objetos.
