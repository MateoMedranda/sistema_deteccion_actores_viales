# Evidencia de implementación y validación — 006

Fecha: 2026-11-20. Checkout principal: C:/Users/USER/Desktop/Mateo/GESTIÓN DE PROYECTOS. Rama conservada: feature/006-mejoras-frontend. Base Git: 432cfd0; cambios de esta ejecución sin commit.

## Estado de aceptación

Frontend y paquetes B1–B5 implementados. La aceptación integral sigue **parcial** por T067 (conjunto/comparación real completos) y T068 (participantes). No se considera satisfecho el seguimiento real en imágenes: DEP-001 continúa fuera de alcance y la UI utiliza Detección N.

## Entorno y comandos realmente ejecutados

Python 3.12.15 del entorno existente .venv; Node 26.7.0, npm 11.19.0, Vite 5.4.21, Vitest 2.1.9 y Playwright 1.65.1. Chromium instalado con npx playwright install chromium. Versiones exactas de modelos/librerías y parámetros no sensibles: [real-model-smoke.json](real-model-smoke.json).

| Comprobación | Comando desde raíz, salvo indicación | Resultado |
|---|---|---|
| Base previa a cambios | .venv/Scripts/python.exe -m pytest | 101 pasaron |
| Backend final | .venv/Scripts/python.exe -m pytest --disable-warnings | 160 pasaron; 2 avisos de dependencias; 27.76 s |
| Frontend | npm --prefix frontend run test | 52 pasaron en 19 archivos |
| Compilación | npm --prefix frontend run build | Correcta, TypeScript y Vite |
| Navegador completo | npm --prefix frontend run test:e2e | 93 pasaron en Chromium, 360/768/1440; 124.4 s |
| Regresión final de sesión/video | test:e2e con video-count-regression y session-lifecycle | 6 pasaron después de corregir expiración terminal; 28.4 s |
| Diseño compacto | test:e2e con visual/accessibility/selection/details | 21 pasaron después de ajustes visuales |
| API real de pruebas | Uvicorn 8767 + Vite 4173 gestionados por Playwright | Arranque aislado y sin reutilizar servidores personales |
| Postman | postman status | CLI disponible; sin sesión ni workspace. No se publicó ningún recurso; verificación HTTP con TestClient y Chromium |

Los logs locales de ejecución están ignorados; las capturas sintéticas seleccionadas quedan en validation-assets/. No hay snapshots aprobados automáticamente ni cambios de package-lock.json.

## Checkpoints funcionales

- T033: una activación produce POST de imagen y POST de enriquecimiento; protección sincrónica ante doble pulsación, vacío sin crear trabajo y fallo posterior conserva detección. Timeouts individuales 120/15/10/30 segundos; ciclo de consulta monotónico de 120 segundos acotado por el menor TTL. Reanudar consulta el mismo job, sin POST automático adicional.
- T040: recuadros y lista comparten ID/selección; Enter y Espacio conservan foco. Selección disponible durante processing. Proyección porcentual sobre el área real de la imagen, con proporción conservada en tres viewports. Nunca se presenta detection_id como Track ID.
- T048: prueba con 55 vehículos sintéticos en dos páginas, resultados desordenados y unión por ID, no por posición. Se rechazan clases/fuentes sin correspondencia. Pruebas de geometría y píxeles del crop 275×280; placa relativa al crop vehicular, límites/degeneradas y compensación únicamente del error de representación IEEE-754. EXIF 1–8 se valida contra píxeles canónicos en backend.
- T056: teclado, controles equivalentes de >=44×44, foco visible, texto 200%, ausencia de desbordamiento global y movimiento reducido en tres viewports. Contraste calculado de muestras de texto >=4.5:1 y color de controles/foco >=3:1; esto no certifica conformidad WCAG completa.
- T063/T064: video H.264 controlado → anotación → línea → conteo → enriquecimiento de video contra backend real de pruebas. Reset/cambio de identidad desmonta estados, detiene consultas y revoca URLs; respuesta tardía de POST de imagen/video no restaura datos y el ID recibido tarde se intenta cancelar. Cancelación remota best-effort, sin bloquear limpieza local.
- Purga: janitor periódico independiente del tráfico, prueba de desaparición de evidencia <=2 s, tombstones por dueño (410) y 404 ajeno; transiciones terminales atómicas y worker cooperativo impiden publicación tardía.
- Privacidad: localStorage/sessionStorage/IndexedDB vacíos después del recorrido y reset; credenciales en memoria y encabezados solo al origen configurado, redirects rechazados; errores seguros. Los datos OCR no read se redactan antes de persistencia JSON/tablas/respuestas y también en el parser del cliente.

La máquina del frontend usa phase para el estado visible y enrichmentStage para submitting/queued/processing; presencia de response diferencia fallo de detección frente a fallo posterior. AbortController, timers y registro de URLs viven en una operación privada al hook, no en estado persistido.

## Revisión visual

Revisión directa de capturas de escritorio, tablet y móvil: jerarquía, colores sólidos, contraste, recuadros, lista, ficha y recortes. Correcciones: desbordamiento móvil con texto 200%, badge de detección partido y exceso de espacio de carga tras completar. Capturas de inicial/completado y estados detecting/enriching/partial/empty/error/cancelled/interrupted/expired generadas con medios sintéticos; ninguna placa real se incorpora a capturas versionadas.

## Comprobación de modelos reales — T067 parcial

Los pesos configurados existen y cargaron: detección y las tres capacidades devolvieron ready. Se ejecutó scripts/validate_frontend_models.py con manifiesto de rutas local no versionado, almacenamiento temporal aislado y credencial sintética. No se cambiaron pesos, modelos ni umbrales.

Se encontraron 6 imágenes locales en el repositorio de los modelos aprobados, no un conjunto etiquetado de 10 escenas viales. Todas devolvieron HTTP 200 y original protegido 200. Una imagen produjo 16 vehículos elegibles y 16 fichas completas de atributos: placas 2 read, 8 unreadable y 6 not_detected. Los otros cinco medios no aportaron vehículos elegibles. Estos conteos no demuestran precisión OCR ni detección.

Mediciones de la última ejecución:
- Detección: 6 muestras, 220.494–376.12 ms de contexto; HTTP incluye validación/transferencia y calentamiento (387–1047 ms aproximadamente).
- Atributos: 16 muestras, 48.099–272.113 ms.
- Enriquecimiento completo de 16 vehículos: 3294.453 ms.
- Pico RSS observado del proceso: 1202.55 MB. Es memoria compartida del proceso, no asignación exclusiva por trabajo. Muestras inicial/final/máximo y demás ramas disponibles en JSON.
- Se conservaron métricas por cuadro de video en regresión controlada; la evaluación comparativa con video vial real sigue pendiente.

Falta: 10 imágenes/20 vehículos con referencia, video vial autorizado, comparación antes/después en iguales condiciones, revisión de calidad, memoria tras ciclos repetidos. No se certifica ausencia de retención creciente a partir de este smoke test.

## Trabajo externo pendiente

T067 permanece abierto con la evidencia parcial anterior. T068 permanece abierto según [usability.md](usability.md). La automatización no sustituye participantes, datos etiquetados ni línea base. La trazabilidad final está en [audit.md](audit.md).

Revisión final adicional: se corrigió la expiración de conteos completados y previews de video; prueba unitaria negativa observada antes de la corrección. Capturas finales sintéticas y un índice de los ocho estados por viewport guardados en validation-assets/.


## Revisión visual registrada

Se inspeccionaron las capturas inicial/completa y el índice de ocho estados en escritorio, tablet y móvil. Se corrigieron el desbordamiento al 200%, las etiquetas partidas de la lista y el exceso de espacio de carga tras analizar. La escena mantiene su proporción; la ficha pasa debajo en pantallas estrechas y el foco permanece en el control activado. Las capturas de estados controlados pueden contener datos sintéticos distintos del recorrido integrado.

- [Escritorio completo](validation-assets/desktop-completed.png)
- [Móvil completo](validation-assets/mobile-completed.png)
- [Estados de escritorio](validation-assets/desktop-states-review.png)
- [Estados de tablet](validation-assets/tablet-states-review.png)
- [Estados de móvil](validation-assets/mobile-states-review.png)

La inspección y las mediciones de contraste muestreadas no certifican conformidad WCAG completa. Las referencias visuales no se aprobaron por actualización automática de snapshots.


## Correcciones de convergencia completadas

T070–T082 cerradas. Consultar [convergence-validation.md](convergence-validation.md) para el mapa de correcciones, pruebas y limitaciones. SC-002 queda verificado con 10 escenas/20 vehículos sintéticos y 55 resultados paginados en navegador; SC-003 dispone ahora de 18 mediciones de 71.4–87.4 ms con datos cargados. Esto no cierra la comparación de modelos reales de T067 ni la evaluación humana de T068.

## Cierre posterior de T083

La métrica del trabajo refleja el desenlace atómico de finish, incluyendo cancelación/vencimiento justo antes de guardar y TTL durante la persistencia; las inferencias terminadas conservan completed. Seis escenarios nuevos, cuatro reproducciones fallidas antes del arreglo y seis aprobadas después. Backend completo: **166 aprobadas**, 2 avisos de dependencias, 22.70 s; frontend: **52 aprobadas**; navegador integrado imagen/video/conteo: **9 aprobadas** en escritorio/tablet/móvil, 39.80 s. La suite previa completa de 93 casos no se vuelve a atribuir a esta ejecución. Detalle en [convergence-validation.md](convergence-validation.md). Estado vigente: 81/83 tareas; T067 y T068 siguen pendientes.
