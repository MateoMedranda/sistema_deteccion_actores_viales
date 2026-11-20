# Implementation Plan: Exploración visual de imágenes viales enriquecidas

**Branch**: `codex/006-mejoras-frontend` | **Date**: 2026-11-20 | **Spec**: [spec.md](spec.md)
**Input**: Iteración 006 y ampliación del usuario: incluir cambios importantes de backend para que puedan ejecutarse durante implementación. El worktree es opcional; preservar la rama histórica y todo archivo ajeno.

## Summary

Crear un recorrido de imágenes profesional: carga y vista previa → detección → enriquecimiento automático → selección del vehículo sobre la imagen → ficha con atributos y evidencia recortada. Colores sólidos, controles claros, acceso por teclado/toque y distribución adaptable. Conservar video y conteo, con correcciones transversales de limpieza de sesión pero sin rediseñarlos.

El backend participa en esta iteración: imagen canónica y cajas coherentes, acceso protegido al original canónico, elegibilidad y vencimiento explícitos, disponibilidad real por rama, saneamiento de placas, transiciones atómicas y limpieza periódica. No se cambian pesos, clases, umbrales, algoritmos ni autenticación.

Una imagen estática utiliza «Detección N». No se creará un `track_id` ficticio. El seguimiento temporal real queda fuera del trabajo implementable de imágenes; se conserva la posibilidad de mostrarlo solo si una fuente lo entrega realmente.

## Technical Context

**Language/Version**: TypeScript ~5.6, React 18.3; Python >=3.12 según `pyproject.toml`.
**Primary Dependencies**: Vite 5.4, CSS existente, React DOM; FastAPI >=0.115,<0.116, Pydantic 2 mediante dependencias existentes, Pillow >=10,<12, OpenCV >=4.10,<5, SQLite estándar. Confirmar versiones exactas desde los lockfiles al implementar; no actualizar dependencias por esta planificación.
**Storage**: Estado React y recursos Blob solo durante la sesión; originales canónicos temporales y SQLite existentes en backend. No añadir base de datos, historial ni persistencia del navegador.
**Testing**: Vitest + Testing Library + Playwright ya declarados; pytest/httpx y pruebas de contrato, integración, concurrencia y regresión existentes. Crear configuración de frontend y pruebas significativas, hoy ausentes.
**Target Platform**: Navegadores de escritorio y móviles modernos; evaluación en 360/768/1440 CSS px, texto 200%, teclado y toque. Servicio local Windows/Python; evitar dependencias exclusivas de plataforma.
**Project Type**: Aplicación web React con microservicio FastAPI modular existente.
**Performance Goals**: Ficha con datos cargados en <1 s; evitar inferencias duplicadas por clic; limpieza de vencidos en <=2 s sin tráfico. Los tiempos de inferencia se medirán sobre el dispositivo real, sin prometer latencias nuevas del modelo.
**Constraints**: Sin gradientes; contraste 4.5:1 texto y 3:1 controles/foco; objetivos táctiles principales 44x44 px; sin secretos en URLs, registros o almacenamiento persistente; mismo propietario y TTL en nueva evidencia; ausencia de datos se representa explícitamente.
**Scale/Scope**: Una imagen activa, una selección y un enriquecimiento activo por recorrido; paginación completa para >50 resultados. Video conserva el límite de una fuente activa de 005. No establecer nuevos límites arbitrarios del backend.

## Constitution Check

| Principio | Antes de investigación | Después de diseño |
|---|---|---|
| I. Modularidad y contratos | PASS: conservar capas y adaptadores existentes. | PASS: DTO tipados, controlador de sesión y geometría separados; contratos aditivos en 006. |
| II. Validación y trazabilidad | PASS: validar imagen/cajas y estados. | PASS: orientación única, cajas no degeneradas, códigos seguros y medidas sin evidencia sensible. |
| III. Seguridad y datos | PASS: mantener propietario, autenticación y temporalidad. | PASS: original protegido, `no-store`, saneamiento previo a toda persistencia, limpieza periódica y revocación de URLs. |
| IV. Pruebas y modelo | PASS: se requieren pruebas proporcionales y regresión imagen/video. | PASS: pruebas por requisito, evidencia controlada y comprobación comparativa de normalización de imagen; sin cambios de pesos o umbrales. |
| V. Rendimiento | PASS: no duplicar inferencia por rediseño. | PASS: crop local, reutilizar original canónico, no endpoint combinado ni publicación incremental compleja. |

No hay excepción constitucional. La ampliación del alcance está autorizada por el usuario y reflejada en FR-025 a FR-033; no requiere modificar la constitución.

## Project Structure

### Documentation (this feature)

```text
specs/006-mejoras-frontend/
  spec.md
  plan.md
  research.md
  data-model.md
  dependencias-backend.md
  quickstart.md
  checklists/requirements.md
  contracts/frontend-interactions.md
  contracts/backend-additions.md
  contracts/openapi-additions.yaml
  tasks.md                        # se generará con speckit-tasks; no creado aquí
```

### Source Code (repository root)

```text
frontend/
  src/App.tsx                     # ciclo común de sesión e invalidación
  src/components/                 # paneles existentes de video/conteo preservados
  src/features/image-analysis/    # módulo nuevo
    ImageWorkspace.tsx
    ImageUpload.tsx
    AnalysisProgress.tsx
    AnnotatedImageViewer.tsx
    DetectionList.tsx
    VehicleDetails.tsx
    EvidenceCrop.tsx
    useImageAnalysis.ts
    imageAnalysisReducer.ts
    types.ts
    image-analysis.css
  src/hooks/useSessionLifecycle.ts
  src/hooks/useObjectUrl.ts
  src/services/apiClient.ts
  src/services/apiTypes.ts
  src/utils/imageGeometry.ts
  src/styles.css
  tests/                         # unidades/componentes y fixtures sintéticos
  e2e/                           # recorridos y capturas controladas
  playwright.config.ts
  vite.config.ts
app/
  api/routes/detections.py        # original canónico protegido y metadatos
  api/routes/health.py            # disponibilidad veraz
  domain/schemas.py              # extensiones aditivas y validación
  services/image_validation.py
  services/image_geometry.py     # geometría canónica compartida nueva
  services/detection_service.py
  services/image_detection_store.py
  services/vehicle_cropping.py
  services/enrichment_job_service.py
  services/enrichment_job_store.py
  services/enrichment_worker.py
  services/enrichment_results.py # saneamiento compartido nuevo
  core/lifespan.py               # capacidades y tarea de limpieza
  services/temporary_artifacts.py
  services/source_artifacts.py
  services/annotation_service.py # usar mismas cajas/IDs al anotar
tests/                           # raíz real, no subcarpeta de app
```

**Structure Decision**: Ampliar las carpetas actuales; no crear otro proyecto, cliente HTTP, store global o motor de procesamiento. Los nombres nuevos son destinos del futuro desglose de tareas, no archivos ya implementados.

## Phase 0 — Research decisions

Decisiones resueltas en [research.md](research.md): controles HTML sobre la imagen, ficha en flujo, estado por generación, imagen canónica, protocolo de backend aditivo y disponibilidad independiente. La investigación de dos agentes fue solo de lectura. No quedan decisiones técnicas bloqueantes ni marcadores pendientes.

## Phase 1 — Design

### Flujo y estado

- La acción de usuario inicia el POST de detección; un guard sincrónico evita doble clic. No lanzar POST desde un efecto de montaje.
- Al recibir detección: fijar fuente y vigencia, cargar imagen canónica y anotada mediante el cliente autenticado y permitir selección; si hay `enrichment_eligible`, crear un único trabajo.
- Consultar cada 1200 ms sin solicitudes solapadas, detener en estado terminal/410/reset y no inventar progreso. Un error de red interrumpe la espera con opción explícita de reconectar; no crear otro trabajo cuando ya se conoce su ID.
- Resultado durante procesamiento: datos básicos y secciones pendientes. Los resultados enriquecidos se publican al terminar; no se promete publicación incremental por vehículo. «Parcial» significa rama ausente o fallida con información válida conservada.
- Reintento de enriquecimiento repite solo esa etapa. Si un POST de creación tuvo respuesta ambigua, no repetir automáticamente ni afirmar que el servidor no recibió el trabajo.
- Cada carga, cambio de credencial/base, reset o desmontaje invalida una generación; aborta fetch y timers, revoca recursos y limpia todas las selecciones. Un ID remoto que llega tarde se cancela con el cliente anterior cuando aún es posible; nunca restaura la sesión.
- Reset común remonta los paneles por generación y recoge canceladores de video/conteo/enriquecimiento con `Promise.allSettled`, sin esperar para limpiar la vista. No confundir abortar HTTP con cancelar un trabajo remoto.

### Diseño visual y accesibilidad

- Fondo gris claro, tarjetas blancas, texto azul oscuro, acento azul sólido y estados con texto/icono. Espaciado 8/16/24/32 px; sin gradientes ni bloques JSON de resultados de imagen.
- Escena predominante y ficha de aproximadamente 340 px al lado en escritorio; una columna en tablet/móvil. Cabeceras, botones y tarjetas admiten salto de línea.
- Imagen anotada como escena; botones transparentes sobre su rectángulo real, con etiqueta accesible estable, `aria-pressed`, foco y hover. Lista equivalente siempre disponible con controles 44x44; no ampliar áreas sobre vehículos vecinos.
- Un `selectedDetectionId` gobierna recuadro/lista/ficha. No se mueve foco al llegar datos. Panel de detalle en flujo, sin modal obligatorio.
- Extraer vehículo del original canónico con caja compartida; extraer placa desde ese recorte y `bbox_relative`, usando truncado/clamp consistente y sin completar detalles. Generar únicamente los recortes necesarios para la selección activa.

### Backend implementable

| Paquete | Cambio concreto | Archivos principales | Criterio de cierre |
|---|---|---|---|
| B1 Geometría canónica | Aplicar orientación EXIF una vez, RGB y eliminar metadatos; generar bytes PNG canónicos acotados por límites de imagen; detección, anotación y enriquecimiento usan esos mismos píxeles. Normalizar/clamp y rechazar cajas degeneradas antes de asignar IDs. | image_validation, image_geometry, detection_service, image_detection_store, vehicle_cropping, annotation_service | Fixtures EXIF 1–8 y bordes; ninguna diferencia de región entre cajas publicadas y crop. |
| B2 Evidencia y elegibilidad | Añadir `source_expires_at`, `original_image` y `enrichment_eligible`; nuevo GET protegido del original canónico, reutilizando almacenamiento de fuente; sin endpoints de crop separados. Unificar vencimiento fuente/anotación o publicar su mínimo efectivo. | schemas, detections, detection_service, image_detection_store, temporary_artifacts | Misma clave requerida, 404 ajeno, 410 dueño vencido, `Cache-Control: no-store`; sin rutas privadas. |
| B3 Disponibilidad | Calcular capacidades a partir de adaptadores realmente inicializados, no de ausencia de configuración. Ampliar respuesta de health con ramas; conservar ready/503 global. Aceptar enriquecimiento parcial cuando una rama sirve; rechazar 503 seguro si ninguna puede servir. | lifespan, health, enrichment_job_service, enrichment_processing | Casos sin modelos, solo atributos, solo placas y completos; detección independiente. |
| B4 Integridad de resultados | Sanear una representación única antes de tabla/JSON/respuesta; texto solo `read`. Cada vehículo elegible produce registro, incluso si su recorte falla. Validar asociación y cajas. | enrichment_results, enrichment_job_store, enrichment_worker, schemas | Ninguna fuga en JSON/tablas/respuestas; identidad estable y estados por rama. |
| B5 Ciclo de vida | Transiciones bajo transacción/bloqueo; finalizar/fallar solo desde processing vigente; cancelación elimina toda representación sensible. Worker revisa estado/TTL entre unidades y antes de publicar. Tarea periódica de limpieza cada 1 s con cierre coordinado. | enrichment_job_store, enrichment_worker, image_detection_store, lifespan | Cancel/finish y TTL/finish concurrentes no resucitan resultados; purga <=2 s sin tráfico. |

Conservar la localización de placa aunque falle OCR. No publicar recortes mejorados como si fueran el original; `used_enhancement` sigue describiendo el OCR existente. Los bloqueos no envolverán inferencia ni bucles largos. El janitor no prolonga TTL y coordina lectura/borrado de archivos; una inferencia ya iniciada puede acabar en memoria sin publicar tras vencimiento.

### Orden de implementación para tasks

1. Contratos/fixtures y backend B1+B2: bloquean geometría y recortes definitivos; pruebas antes de cada modificación de comportamiento.
2. Backend B3+B4+B5 y sus pruebas de concurrencia/privacidad; estos paquetes comparten store/worker y no deben editarse en paralelo sin coordinación.
3. Tipos, ApiClient compatible, geometría y ciclo de sesión común; conservar interfaces de video con parámetros opcionales nuevos.
4. Orquestación de imágenes, visor/lista/ficha y recortes; desarrollar con fixtures fieles a los contratos sin presentarlos como servicio real.
5. Estilos, estados, responsive y accesibilidad; capturas revisadas en todos los tamaños.
6. Integración real, regresión de imagen/video/conteo, mediciones y evaluación de uso de la especificación. Cerrar solo con evidencia.

## Validation strategy

- Unitarias frontend: geometría/crops con cuadrantes de colores, reducer, duplicación, respuestas tardías, polling, revocación y paginación >50.
- Componentes: teclado Enter/Espacio, selección sincronizada, foco estable, placas ilegibles con recorte, fallos independientes y estados vacíos.
- Backend: EXIF y geometría, contrato aditivo, original protegido/TTL, readiness real, redacción de todas las representaciones, concurrencia y purga sin tráfico con reloj controlado.
- E2E: frontend con backend de pruebas y adaptadores deterministas para recorrido integrado; suite visual con fixtures sintéticos del cliente. Validación separada con modelos reales y medios controlados; falta de recursos privados no se sustituye por afirmar éxito.
- Regresión: suites existentes de imagen/video/conteo y pruebas de CORS; no rediseñar video. Medir efecto de normalización en imágenes aprobadas y documentar diferencias antes de aceptar una degradación.
- Las comprobaciones y comandos están en [quickstart.md](quickstart.md). Este comando de planificación no ejecuta pruebas de producto ni acredita criterios de aceptación ya cumplidos.

## Complexity Tracking

Sin violaciones constitucionales ni nuevas dependencias de producción. Se descartan endpoint combinado, base nueva, seguimiento ficticio, framework de estado adicional y publicación incremental para mantener el alcance.
