# Trabajo de backend incluido — Iteración 006

**Actualizado**: 2026-11-20.
**Cambio de alcance autorizado**: el usuario pidió incluir cambios importantes del backend para ejecutarlos junto con la implementación. Ya no son incidencias que esta rama solo pueda delegar; los paquetes B1–B5 forman parte del plan. Esta ejecución modifica documentación, no código de aplicación.

## Hallazgos y resolución planificada

| Referencia | Hallazgo en código | Resolución en 006 |
|---|---|---|
| DEP-001 Identidad | Imagen expone detection_id; enriquecimiento usa track_id=null. | Preservar identidad real por fuente/detección. No crear seguimiento ficticio. El tracking temporal real sigue fuera de alcance. |
| DEP-002 Geometría/evidencia | PIL conserva dimensiones sin transposición explícita; OpenCV decodifica por separado. Respuesta fuerza cajas degeneradas mientras crop las rechaza. | B1 imagen canónica/orientación única y geometría compartida; B2 ruta protegida del original, metadatos de TTL/elegibilidad. |
| DEP-003 Enriquecimiento | Readiness puede indicar listo sin adaptadores; JSON crudo puede conservar texto que la tabla redacta; finalización/cancelación tienen carreras. | B3 disponibilidad por rama y procesamiento parcial útil; B4 saneamiento único; B5 transiciones y purga coordinadas. |
| DEP-004 Acceso/TTL | La limpieza de originales depende de llamadas; nueva evidencia debe usar permisos existentes. | Janitor 1 s, objetivo <=2 s, propiedad y tombstones por dueño, no-store y recursos efímeros en UI. |

## Evidencia inspeccionada

- `app/services/image_validation.py`: dimensiones de upload y bytes originales sin normalización EXIF explícita.
- `app/services/detection_service.py`: decodificación independiente, almacenamiento de fuente y clamp distinto del recorte.
- `app/services/vehicle_cropping.py`: recorta usando truncado entero, clamp y rechaza degeneradas.
- `app/services/enrichment_job_service.py`: conserva índices de detección al filtrar; usa track_id null para imagen.
- `app/services/enrichment_processing.py`: caja de placa normalizada al crop vehicular; conserva localización en algunos fallos de OCR, pero el guard inicial exige localizer y reader a la vez.
- `app/core/lifespan.py`: readiness por ausencia de configuración; no janitor periódico de fuentes.
- `app/services/enrichment_job_store.py`: JSON/table saneados de forma desigual, transiciones a revisar y limpieza al acceder.
- `frontend/src/services/apiTypes.ts`: tipo de detección plana distinto del DTO real.
- `frontend/src/App.tsx`: reset limpia estado de App pero no garantiza desmontar/limpiar estados internos.

Son hallazgos de lectura, no incidentes reproducidos mediante pruebas nuevas. Las pruebas de implementación deberán confirmar y cerrar cada caso.

## Límites y prerrequisitos

- No se entrenan ni sustituyen modelos, pesos, umbrales ni OCR aprobado. Se conservan las correcciones ALPR confirmadas.
- Pesos/manifiestos privados y medios autorizados deben existir en el entorno para validar modelos reales; fixtures deterministas verifican integración y UI sin afirmar calidad del modelo.
- No se crea endpoint combinado ni endpoints de crop separados. El original canónico ya necesario para enriquecimiento se expone con autorización y la misma temporalidad.
- Publicación enriquecida al completed; durante processing se muestran datos básicos y secciones pendientes. Incremental por vehículo e idempotencia persistida se difieren.
- Video/conteo conservan sus contratos; solo se corrigen limpieza y recursos comunes cuando el cambio lo exige.

## Rama y continuidad

El trabajo se inició en `feature/006-mejoras-frontend` desde `81bc12d`. El backend confirmó después `6f0243a`, que añade diagnóstico y auditoría de ALPR sin cambiar los contratos estudiados. Antes de retirar el worktree se preservará la documentación y se incorporará ese commit de forma explícita; no se incorporarán archivos sueltos ni se sobrescribirán sesiones ajenas. Continuar en una rama separada del checkout principal está autorizado y no exige mantener un worktree adicional.

## Referencias ejecutables posteriores

- [plan.md](plan.md): paquetes B1–B5, secuencia y archivos afectados.
- [backend-additions.md](contracts/backend-additions.md): comportamiento y errores.
- [openapi-additions.yaml](contracts/openapi-additions.yaml): ruta y campos propuestos.
- [quickstart.md](quickstart.md): verificaciones; no se han ejecutado como parte de planificación.
