# Correcciones de convergencia T070–T083

Fecha local de ejecución: 2026-11-20. Checkout principal y rama feature/006-mejoras-frontend conservados. No se crearon commits. No se cambiaron pesos, modelo, umbrales ni valores privados de configuración.

## Resultado

Las 14 correcciones están implementadas y verificadas. Hay 81/83 tareas completadas; T067 y T068 siguen pendientes. T083 cierra el caso residual de finalización de métricas detectado al revisar T080. Este informe sustituye las limitaciones de implementación señaladas en Phase 9; esa sección conserva la descripción histórica de los hallazgos.

| Tarea | Corrección y prueba |
|---|---|
| T070 | HTTP 401/404/410 conserva su estado, cierra transporte/cuerpo y retira datos sin esperar otra descarga. Regresiones con ambos órdenes, cuerpo suspendido y respuesta tardía. |
| T071 | Recibos mínimos de propiedad/vencimiento escritos antes de los bytes; el janitor los reconoce tras reiniciar. Pruebas de dos instancias, purga sin tráfico, deadline reducido y archivos ajenos preservados. |
| T072 | Normalización Pillow ejecutada en threadpool; prueba con barrera permite responder otra petición durante normalización y conserva EXIF/límites. |
| T073 | Señales opcionales compatibles para video/conteo/enriquecimiento, aborto por generación y TTL, cancelación remota best-effort y limpieza ante rechazo. Chromium prueba reset/cambio de credencial/base antes del ID, cancelación fallida y video rechazado. |
| T074 | Cada intento elimina ID/progreso anteriores. La fuente se registra en la operación, independiente del render de React; creación ambigua no reanuda un job viejo ni reenvía POST automáticamente. |
| T075 | Original y anotación tienen estados propios, validación de decodificación/dimensiones y recuperación por medio sin otra inferencia. Chromium verifica bytes inválidos y reintento. |
| T076 | GET /health/image-policy expone solo formatos y límites ya configurados; el frontend muestra valores efectivos y declara si no puede obtenerlos. Pruebas con configuraciones distintas. |
| T077 | Borrar línea invalida al padre; cambiar video reinicia puntos/arrastre. Chromium confirma cero POST de conteo después de borrar y ausencia de trazos/configuración de la fuente anterior. |
| T078 | Contorno y foco de dos colores, selección con símbolo y lista equivalente. Se miden estilos reales sobre blanco/negro; se prueba toque y cajas pequeñas/solapadas. |
| T079 | Envío, cola y procesamiento tienen títulos/anuncios distintos; no se inventa porcentaje. |
| T080 | Métricas de unidad reflejan cancelación/TTL antes de inferir y entre evidencias, sin alterar la finalización real de ramas que ya terminaron. |
| T081 | Diez escenas/veinte vehículos con píxeles y atributos distinguibles; 55 resultados en dos páginas, orden inverso e IDs no consecutivos. Comparación de píxeles vehiculares y de placa, cuatro estados y canario no read ausente. |
| T082 | 18 mediciones de selección/ficha/recorte local con datos cargados, reloj monotónico y umbral <1 s, seis por viewport. Evidencia en loaded-detail-latency.json. |

## Comandos y resultados de T070–T082

| Ejecución | Resultado |
|---|---|
| .venv/Scripts/python.exe -m pytest --disable-warnings | 160 pasaron, 2 avisos de dependencias, 27.76 s |
| npm --prefix frontend run build | TypeScript y Vite correctos |
| npm --prefix frontend run test | 52 pasaron en 19 archivos |
| npm --prefix frontend run test:e2e | 93 pasaron; 0 omitidos, 0 inesperados y 0 flaky; 124.4 s |
| Regresión final de acceso/medios/sesión | 24 pasaron tras cerrar también el transporte HTTP rechazado |
| Regresión final de estados/visual/flujo | 30 pasaron tras registrar la fuente fuera del ciclo de render |

Las regresiones críticas se ejecutaron antes de corregir el código y reprodujeron los defectos. Las suites integradas usan API real de pruebas con adaptadores sintéticos; otras pruebas de interfaz usan respuestas controladas. No certifican precisión de modelos.

## Latencia de ficha con datos disponibles

| Proyecto | Viewport CSS | Muestras | Mínimo–máximo |
|---|---|---:|---|
| Escritorio | 1440×1000 | 6 | 72.3–86.8 ms |
| Tablet táctil | 768×1024 | 6 | 73.5–87.4 ms |
| Móvil táctil | 360×800 | 6 | 71.4–85.3 ms |

Incluye selección, identidad correcta, ficha y crop local. Excluye inferencia y descarga inicial ya completadas. Hardware, navegador y condiciones están registrados en [loaded-detail-latency.json](loaded-detail-latency.json). Estas mediciones no representan tiempo total de análisis ni evaluación con personas.

## Límites y conservación

Los recibos contienen únicamente versión y vencimiento; no guardan placas, imágenes, credenciales ni rutas. El plazo publicado puede reducirse y nunca se amplía al recuperar o consultar. La evidencia no recuperable por metadata perdida no se vuelve accesible al reiniciar; su archivo se elimina al vencer el plazo original.

No se borran ciegamente archivos históricos sin recibo, porque su propiedad no puede demostrarse. Se preservan para revisión local. La purga tras reinicio de esta corrección cubre archivos gestionados desde esta versión y probados con dos instancias sucesivas; no promete eliminación mientras el proceso está detenido.

La cancelación remota sigue siendo best-effort y no implica interrumpir una inferencia ya iniciada. La retirada local y la prohibición de publicación tardía se prueban por separado.

T067 aún requiere datos de referencia y comparación real completa; T068 requiere cinco participantes. DEP-001 sigue pendiente y las imágenes estáticas mantienen Detección N.

## Finalización atómica y métricas — T083

`EnrichmentJobStore.finish(...)` devuelve el estado confirmado bajo el mismo bloqueo que valida/publica el resultado: completed cuando guarda, cancelled si ganó la cancelación y expired cuando el TTL impidió publicar. El worker usa ese retorno para la métrica enrichment_job. No consulta un estado posterior que pueda confundir una limpieza ulterior con el desenlace de publicación; las métricas de unidades y ramas ya finalizadas conservan completed. Las excepciones y las protecciones de publicación existentes se mantienen.

Se añadieron seis escenarios deterministas en tests/unit/test_worker_unit_metrics.py, con SQLite temporal real, reloj inyectado y adaptadores sintéticos existentes: éxito, cancelación justo antes de finish, TTL antes de finish, TTL durante la persistencia, TTL/limpieza después del commit y TTL/limpieza después de una cancelación confirmada. Antes del arreglo fallaron cuatro por registrar completed incorrectamente. Después pasan los seis; verifican todas las tablas/JSON, 410 del dueño vencido, correlación, duración/RSS y ausencia de placa/ruta privada en logs. No se usaron pesos ni configuración privada.

| Ejecución posterior a T083 | Resultado |
|---|---|
| pytest tests/unit/test_worker_unit_metrics.py tests/unit/test_enrichment_lifecycle.py tests/unit/test_enrichment_worker_cancellation.py tests/unit/test_enrichment_results.py tests/unit/test_inference_observability.py -p no:cacheprovider --disable-warnings --tb=short -q | 29 aprobadas |
| .venv/Scripts/python.exe -m pytest -p no:cacheprovider --disable-warnings | 166 aprobadas, 2 avisos de dependencias, 22.70 s |
| npm --prefix frontend run test -- --no-cache | 52 aprobadas en 19 archivos |
| Playwright image-analysis.flow.spec.ts y video-count-regression.spec.ts | 9 aprobadas, 0 omitidas/inesperadas/flaky, 39.80 s; escritorio/tablet/móvil |

La suite completa de 93 casos de navegador pertenece a la verificación anterior; tras este cambio interno del worker se reejecutaron los 9 recorridos integrados pertinentes. Los reportes/capturas nuevos se guardaron en el directorio temporal. No se modifica API HTTP, autenticación, modelos, límites ni el frontend. Rama feature/006-mejoras-frontend y cambios anteriores conservados; sin commits. Estado: 81/83; T067 y T068 pendientes.
