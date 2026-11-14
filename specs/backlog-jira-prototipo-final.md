# Backlog Jira — prototipo final de detección vial

**Proyecto:** Sistema de detección de actores viales  
**Propósito:** planificar la evolución desde la primera iteración de análisis de imágenes hacia un prototipo que procese imágenes y videos, obtenga características y placas, y cuente actores viales por línea virtual.

## Criterio de planificación

- Las claves `SAV-xxx` son sugeridas: Jira asignará las claves reales al crear las incidencias.
- Los puntos son **Story Points de Jira**, no horas ni PTS de `speckit-metricas`.
- Las historias de placas requieren una revisión de autorización, privacidad y retención antes de implementarse.
- El procesamiento de video y el conteo dependen de un rastreador multiobjeto: una detección de un solo fotograma no permite contar cruces de forma confiable.

## Orden recomendado de releases

1. **R1 — Cierre del backend de imágenes:** completar validación, pruebas y métricas de la API.
2. **R2 — Video anotado:** carga, procesamiento asíncrono, detección por fotograma y resultado reproducible.
3. **R3 — Conteo por línea:** rastreo, líneas configurables y eventos de cruce.
4. **R4 — Atributos y placas:** extracción de características, detección/OCR de placas y controles de privacidad.

## Cronograma acelerado — entrega del backend el 6 de diciembre de 2026

**Supuesto de planificación:** un desarrollador con apoyo de IA, dedicación de aproximadamente 25 horas por semana y una velocidad objetivo de **18 Story Points por sprint**. Son tres sprints: la meta es un **MVP demostrable**, no la totalidad de las 93 SP del producto final.

| Sprint | Fechas | Objetivo de entrega | Incidencias Jira |
|---|---|---|---|
| 1 | 27 oct. – 9 nov. | API de imágenes cerrada y preparada para ser consumida por una UI posterior | SAV-101 y preparación de SAV-201 |
| 2 | 10 – 23 nov. | Carga de video, trabajo asíncrono, video anotado y pistas con ID | SAV-201, SAV-202, SAV-203, SAV-204 |
| 3 | 24 nov. – 6 dic. | Configuración de línea por API, conteo básico por dirección y prueba de demostración de backend | SAV-501, SAV-502, SAV-503 y pruebas críticas de SAV-602 |

**Fecha objetivo del backend funcional:** **6 de diciembre de 2026**.  
**Frontend:** se planificará después de estabilizar y demostrar los contratos de la API.

### Alcance comprometido para el 6 de diciembre

- Carga y análisis de imágenes mediante API documentada.
- Carga de un video, consulta de progreso y recuperación del video anotado mediante API.
- Rastreo básico con `track_id` para los actores viales procesados en el video.
- Configuración de **una línea recta por video** mediante API: dos puntos normalizados, dirección y clases a contar.
- Conteo por clase y dirección al cruzar la línea, sin duplicar el mismo `track_id`.
- Mensajes de error seguros, pruebas críticas y documentación de uso.

### Alcance diferido después del 6 de diciembre

- Todo frontend: carga visual de imágenes y videos, dibujo de líneas, reproductor, tablero y tabla de eventos.
- Extracción de atributos avanzados que requiera un modelo adicional; en el MVP solo se devuelven clase y confianza ya producidas por el detector.
- OCR de placas, almacenamiento de texto de placas, exportaciones con placas o cualquier revelación de datos personales.
- Múltiples líneas por video, cámara en tiempo real, historial avanzado, analítica histórica y calibración exhaustiva del conteo.
- Benchmark completo de precisión de conteo y endurecimiento para producción.

> Esta fecha es viable solo si se respeta el recorte de alcance, se reutiliza el backend de imágenes ya construido y se considera la línea de conteo como una característica de demostración validada con videos cortos. El trabajo diferido permanece en el backlog para la siguiente entrega.

## Épica 1 — Base de detección y experiencia de imágenes

### SAV-101 — Cerrar la primera iteración de análisis de imágenes

**Tipo:** Historia · **Prioridad:** P0 · **Estimación:** 5 SP  
**Historia:** Como responsable técnico, quiero cerrar los hallazgos pendientes de la primera iteración para usar la API de imágenes como base confiable de las funcionalidades posteriores.

**Criterios de aceptación**

- Se completan y evidencian las tareas pendientes T027, T034, T041, T046, T047, T048, T049 y T054.
- Todas las validaciones de carga se registran de forma segura y se rechazan extensiones no permitidas.
- El benchmark conserva métricas de latencia, modelo, dispositivo y p95 sin secretos.

**Subtareas**

- [ ] Ejecutar y documentar pruebas unitarias, de integración y contrato de imágenes.
- [ ] Completar registros seguros de rechazos y cobertura de extensiones.
- [ ] Ejecutar benchmark de referencia y adjuntar evidencia al documento de auditoría.

### SAV-102 — Interfaz mínima para analizar una imagen

**Tipo:** Historia · **Prioridad:** P3 · **Estimación:** 5 SP · **Estado:** Diferida hasta estabilizar el backend  
**Historia:** Como usuario, quiero cargar una imagen y visualizar las cajas, clase, confianza y resumen de detecciones sin invocar la API manualmente.

**Criterios de aceptación**

- La UI consume únicamente el contrato público de la API.
- Presenta estados de carga, éxito, imagen anotada y error seguro.
- No expone la API key ni rutas internas en el navegador.

**Subtareas**

- [ ] Diseñar una pantalla de carga y resultado en `ui/`.
- [ ] Implementar un cliente autenticado mediante backend/BFF, sin secretos en frontend.
- [ ] Añadir prueba de consumo de contrato y prueba manual de accesibilidad básica.

## Épica 2 — Procesamiento de videos

### SAV-201 — Recibir y validar un video vial

**Tipo:** Historia · **Prioridad:** P1 · **Estimación:** 5 SP  
**Historia:** Como usuario, quiero cargar un video de una vía para enviarlo a procesamiento sin que archivos corruptos o excesivos afecten el servicio.

**Criterios de aceptación**

- Se aceptan solo contenedores, códecs, duración, tamaño y resolución configurados.
- La respuesta crea un identificador de trabajo sin bloquear la solicitud HTTP hasta terminar el video.
- Los errores informan la causa de forma segura y eliminan archivos temporales fallidos.

**Subtareas**

- [ ] Definir límites de video y esquema `VideoAnalysisJob` en `app/domain/models.py`.
- [ ] Crear `POST /v1/videos` y validación en `app/services/video_validation.py`.
- [ ] Añadir pruebas de formatos, tamaño, duración, corrupción y limpieza.

### SAV-202 — Procesar un video como trabajo asíncrono

**Tipo:** Historia · **Prioridad:** P1 · **Estimación:** 8 SP  
**Historia:** Como usuario, quiero conocer el estado y progreso del análisis de mi video para esperar el resultado sin perder el control de la solicitud.

**Criterios de aceptación**

- El trabajo pasa por estados `queued`, `processing`, `completed`, `failed` o `cancelled`.
- `GET /v1/videos/{jobId}` informa porcentaje, mensajes seguros y resultado cuando corresponde.
- El modelo se reutiliza y el número de trabajos concurrentes se limita por configuración.

**Subtareas**

- [ ] Implementar cola/worker local o servicio de trabajos definido en `app/services/video_jobs.py`.
- [ ] Crear rutas de consulta y cancelación del trabajo.
- [ ] Registrar tiempos por etapa y probar recuperación ante error de inferencia.

### SAV-203 — Entregar video y resumen anotados

**Tipo:** Historia · **Prioridad:** P2 · **Estimación:** 5 SP  
**Historia:** Como usuario, quiero reproducir el video anotado y consultar un resumen por clase para interpretar el resultado.

**Criterios de aceptación**

- El resultado incluye URL temporal al video anotado y resumen de detecciones por clase.
- Las cajas, clases y confianzas se corresponden con los fotogramas procesados.
- Los resultados expiran y se eliminan según la política de artefactos.

**Subtareas**

- [ ] Implementar lector/escritor de video en `app/services/video_rendering.py`.
- [ ] Extender los artefactos temporales para video y sus metadatos.
- [ ] Agregar pruebas con un video corto de referencia y verificación de expiración.

### SAV-204 — Asignar un ID persistente a cada actor en video

**Tipo:** Historia · **Prioridad:** P1 · **Estimación:** 8 SP  
**Historia:** Como sistema, quiero asociar detecciones del mismo actor entre fotogramas para habilitar conteo y análisis temporal sin duplicados.

**Criterios de aceptación**

- Cada pista contiene `track_id`, clase, confianza, caja, fotograma y estado.
- El rastreador conserva razonablemente la identidad ante movimiento breve u oclusión corta.
- La configuración documenta el algoritmo y parámetros de rastreo.

**Subtareas**

- [ ] Definir protocolo de rastreador en `app/adapters/tracker_protocol.py`.
- [ ] Implementar adaptador de rastreo seleccionado y sus parámetros configurables.
- [ ] Probar asociaciones, pérdida de pista y reaparición con secuencias de referencia.

## Épica 3 — Características y placas

### SAV-301 — Definir el catálogo de características viales

**Tipo:** Historia · **Prioridad:** P1 · **Estimación:** 3 SP  
**Historia:** Como investigador, quiero un catálogo explícito de características por actor para que el sistema no prometa atributos que el modelo no puede obtener.

**Criterios de aceptación**

- Se documentan atributos, fuente de cada atributo, clases aplicables y confianza mínima.
- Se distingue entre atributo derivado del detector y atributo obtenido por un modelo adicional.
- El contrato marca atributos no disponibles como ausentes, no como valores inferidos.

**Subtareas**

- [ ] Crear `specs/atributos-viales.md` con catálogo y datos de prueba.
- [ ] Actualizar esquemas públicos para `attributes` con procedencia y confianza.
- [ ] Revisar métricas de precisión por atributo antes de aceptar un modelo adicional.

### SAV-302 — Extraer y mostrar características de actores

**Tipo:** Historia · **Prioridad:** P2 · **Estimación:** 5 SP  
**Historia:** Como usuario, quiero consultar las características confiables de cada actor detectado para enriquecer el análisis vial.

**Criterios de aceptación**

- Los atributos se vinculan a una detección o pista mediante un identificador estable.
- La respuesta indica valor, confianza y origen del atributo.
- La UI muestra solo atributos soportados para la clase del actor.

**Subtareas**

- [ ] Implementar servicio/adaptador de atributos en `app/services/attribute_service.py`.
- [ ] Integrar atributos en análisis de imagen y video.
- [ ] Crear pruebas con casos de atributo presente, ausente y de baja confianza.

### SAV-401 — Detectar y recortar placas vehiculares

**Tipo:** Historia · **Prioridad:** P1 · **Estimación:** 5 SP  
**Historia:** Como usuario autorizado, quiero identificar la región de una placa asociada a un vehículo para habilitar su lectura bajo controles definidos.

**Criterios de aceptación**

- La placa detectada se relaciona con el vehículo y fotograma de origen cuando sea posible.
- El resultado conserva la confianza y caja de la placa.
- El recorte no se conserva más tiempo del permitido por la política del proyecto.

**Subtareas**

- [ ] Definir entidad `PlateDetection` y política de retención.
- [ ] Implementar adaptador de detección de placas y pruebas de asociación con vehículo.
- [ ] Registrar métricas de precisión/recall del conjunto de prueba autorizado.

### SAV-402 — Leer placas con OCR y proteger datos personales

**Tipo:** Historia · **Prioridad:** P0 · **Estimación:** 8 SP  
**Historia:** Como responsable autorizado, quiero obtener la lectura de una placa cuando sea legible, preservando la privacidad y trazabilidad de su uso.

**Criterios de aceptación**

- El OCR devuelve texto, confianza y motivo de rechazo si la lectura no es confiable.
- La UI enmascara el texto por defecto; revelar o exportar requiere autorización definida.
- Se registra acceso y se aplica eliminación/retención conforme a la política aprobada.

**Subtareas**

- [ ] Aprobar requisitos legales, roles y política de retención antes de codificar OCR.
- [ ] Implementar `plate_ocr_service.py` y umbral de confianza configurable.
- [ ] Implementar enmascaramiento, autorización, trazabilidad y pruebas de no exposición.

## Épica 4 — Conteo por línea virtual configurable

### Diseño obligatorio del conteo

Una **línea de conteo** se guarda con coordenadas normalizadas (`x1`, `y1`, `x2`, `y2` entre 0 y 1), dirección (`A_TO_B`, `B_TO_A` o `BIDIRECTIONAL`), clases filtradas y un identificador de escena. Esto permite dibujarla sobre una vista previa y conservar su posición aunque cambie la resolución del video.

Un actor cuenta solamente cuando una **pista** con `track_id` cambia de lado respecto de la línea. Cada evento almacena línea, pista, clase, dirección y fotograma. Se aplica una tolerancia alrededor de la línea y se permite un único cruce por `track_id` y línea, salvo una regla posterior explícita de reingreso.

### SAV-501 — Configurar líneas de conteo sobre el video

**Tipo:** Historia · **Prioridad:** P1 · **Estimación:** 5 SP  
**Historia:** Como analista vial, quiero dibujar, mover y eliminar una línea recta sobre un fotograma de referencia para definir el lugar donde se contará el tránsito.

**Criterios de aceptación**

- El usuario selecciona dos puntos con el mouse/táctil y observa una vista previa de la línea.
- Puede indicar dirección, clases a contar y nombre de la línea.
- Al guardar y volver a abrir, la línea aparece en la misma posición relativa del video.

**Subtareas**

- [ ] Crear entidad `CountingLine` y migración/persistencia de configuraciones de escena.
- [ ] Exponer CRUD `POST/GET/PATCH/DELETE /v1/scenes/{sceneId}/count-lines`.
- [ ] Implementar componente de dibujo y edición en `ui/components/CountingLineCanvas`.
- [ ] Probar coordenadas normalizadas, permisos y recuperación de configuración.

### SAV-502 — Detectar eventos de cruce sin doble conteo

**Tipo:** Historia · **Prioridad:** P0 · **Estimación:** 8 SP  
**Historia:** Como analista vial, quiero que el sistema cuente cada actor al cruzar mi línea en la dirección elegida, sin contar varias veces el mismo actor.

**Criterios de aceptación**

- Un evento se genera solo cuando la trayectoria de un `track_id` cruza la línea configurada.
- El evento registra clase, dirección, instante/fotograma y confianza.
- Objetos que permanecen sobre la línea, vibran o se ocluyen no incrementan el contador indebidamente.

**Subtareas**

- [ ] Implementar cálculo de lado de línea y transición en `app/services/counting_service.py`.
- [ ] Añadir zona de tolerancia, memoria de cruces y filtro por dirección/clase.
- [ ] Definir entidad `CountEvent` y almacenamiento de agregados por línea.
- [ ] Crear pruebas con trayectorias sintéticas: cruce válido, ida/vuelta, ruido, oclusión y dos actores.

### SAV-503 — Mostrar conteos y eventos en el resultado

**Tipo:** Historia · **Prioridad:** P1 · **Estimación:** 5 SP  
**Historia:** Como usuario, quiero ver el total por clase y dirección, y revisar los eventos de cruce, para interpretar el flujo vehicular del video.

**Criterios de aceptación**

- El resultado muestra contadores por línea, clase y dirección.
- El video anotado enseña la línea, los IDs de pista opcionales y el contador actualizado.
- Se puede descargar un CSV de eventos sin exponer placas ni datos no autorizados.

**Subtareas**

- [ ] Añadir resumen de conteo y eventos al contrato de video.
- [ ] Renderizar línea y contador en `app/services/video_rendering.py`.
- [ ] Crear endpoint de exportación CSV con controles de autorización.
- [ ] Implementar tarjetas y tabla de eventos en la UI.

### SAV-504 — Validar la exactitud del conteo

**Tipo:** Historia · **Prioridad:** P0 · **Estimación:** 5 SP  
**Historia:** Como investigador, quiero comparar el conteo automático con un conteo manual de referencia para conocer su error y condiciones de uso.

**Criterios de aceptación**

- Existe un conjunto de videos con conteos manuales y líneas de referencia.
- Se reportan conteo real, conteo automático, error absoluto y porcentaje de error por clase/dirección.
- Se documentan cámaras, escenas, oclusiones y otras limitaciones.

**Subtareas**

- [ ] Preparar conjunto de evaluación autorizado y protocolo de anotación manual.
- [ ] Implementar prueba/benchmark de conteo en `tests/performance/test_counting_accuracy.py`.
- [ ] Publicar informe de resultados y parámetros de calibración.

## Épica 5 — Calidad, seguridad y operación

### SAV-601 — Observar el procesamiento extremo a extremo

**Tipo:** Historia · **Prioridad:** P1 · **Estimación:** 5 SP  
**Historia:** Como operador, quiero métricas y registros seguros por imagen, video y conteo para diagnosticar rendimiento sin exponer información sensible.

**Criterios de aceptación**

- Se miden validación, inferencia, rastreo, OCR, renderizado y total.
- Los registros incluyen `request_id`/`job_id`, estado y error seguro, nunca imágenes ni placas completas.
- Hay métricas de p50/p95, trabajos fallidos y cola.

### SAV-602 — Validar rendimiento, seguridad y contratos

**Tipo:** Historia · **Prioridad:** P0 · **Estimación:** 8 SP  
**Historia:** Como responsable de calidad, quiero pruebas repetibles de seguridad, contrato y rendimiento para aceptar el prototipo con evidencia.

**Criterios de aceptación**

- Todas las rutas tienen pruebas unitarias, integración y contrato proporcionales al riesgo.
- Se prueban límites de carga, autorización, expiración, concurrencia y privacidad de placas.
- Se ejecutan benchmarks de imagen, video y conteo en el hardware documentado.

## Dependencias críticas

```text
SAV-101 → SAV-102 (fase posterior de frontend)
SAV-201 → SAV-202 → SAV-203
SAV-202 → SAV-204 → SAV-502 → SAV-503 → SAV-504
SAV-301 → SAV-302
SAV-401 → SAV-402
SAV-201/SAV-202/SAV-204/SAV-401 → SAV-601/SAV-602
```

**MVP de backend recomendado:** SAV-101, SAV-201, SAV-202, SAV-203, SAV-204, SAV-501, SAV-502 y SAV-503. SAV-102 se implementará después como primera historia de frontend. Deja OCR de placas (SAV-402) para después de aprobar privacidad y validar el conteo (SAV-504) como evidencia antes de la demostración final.
