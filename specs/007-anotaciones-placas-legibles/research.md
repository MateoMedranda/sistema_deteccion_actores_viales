# Investigación — 007 Anotaciones despejadas y placas legibles

Fecha: 2026-11-20. Inspección de solo lectura del checkout principal, dos investigaciones delegadas (escena y placas) y documentación primaria. Este documento decide el diseño; no acredita una mejora de exactitud ni mediciones de producto.

## R1. Fondo sin texto integrado

**Decision**: Presentar la imagen PNG canónica de original-image, ya protegida en 006, con una única capa de contornos. No usar annotated-image como fondo ni como fallback automático del nuevo visor. Renderizar también actores no enriquecibles como contornos no interactivos.
**Rationale**: AnnotatedImageViewer añade números sobre una imagen que ya puede traer textos de annotation_service. Ocultar solo el span no elimina la obstrucción. El original conserva geometría y permite mantener píxeles fieles.
**Alternatives considered**: Reducir fuente, evitar colisiones con etiquetas flotantes o esconder solo el HTML no resuelve las dos capas. Regenerar otra anotada sin texto duplica una representación ya innecesaria.
**Evidence**: frontend/src/features/image-analysis/AnnotatedImageViewer.tsx, ImageWorkspace.tsx, useImageAnalysis.ts; app/services/annotation_service.py; app/api/routes/detections.py.
**Compatibility**: Mantener contratos/artefacto annotated-image para clientes previos y video. Si falta original, conservar lista/resultados autorizados y ofrecer reintento del original; no prometer escena despejada en un servicio anterior.

## R2. Contexto y clase

**Decision**: Mantener selectedDetectionId y contexto transitorio separados. Contexto = focusedId ?? hoveredId ?? selectedId, limitado a detecciones de la fuente activa. La banda contextual está fuera del rectángulo de imagen. Eliminar de la escena spans numéricos y glifos textuales de selección; usar bordes/halos geométricos.
**Rationale**: El puntero no debe cambiar ficha, generar peticiones de placa ni competir con el foco del teclado. La lista sigue ofreciendo objetivos de 44 px.
**Alternatives considered**: Tooltip sobre el vehículo, seleccionar en mouseenter, usar solo color y ampliar hitboxes dañan los criterios de identidad/visibilidad.
**Sources**: [W3C: uso de color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html). El texto/nombre y la forma complementarán el color; no se afirma certificación WCAG.

## R3. Catálogo de colores

**Decision**: Un registro explícito por class_name normalizado, compartido por escena/lista/leyenda/ficha; catálogo y colores fijados en contracts/frontend-interactions.md. Cubre las diez clases vehiculares por defecto y person/bicycle/motorcycle. No usar class_id % 8 ni el orden de detecciones. Clases no reconocidas: neutral con nombre real. Añadir una clase configurada conocida exige ampliar el registro y su prueba, no asignar neutral silenciosamente como si estuviera cubierta.
**Rationale**: El backend actual tiene una paleta módulo 8; el overlay blanco del cliente además oculta la clase. La nueva presentación no necesita cambiar detección ni colores de artefactos históricos.
**Alternatives considered**: Hash sin control de colisiones; asignación según clases presentes; paleta diferente para cada componente.
**Evidence**: app/core/config.py (vehicle_classes); annotation_service.py; frontend/src/features/image-analysis/image-analysis.css.

## R4. Vista procesada mínima y conservadora

**Decision**: Un GET PNG protegido por trabajo/detección de imagen, sin pedir coordenadas al cliente, sin volver a ejecutar localizador, detector u OCR. Cabecera X-Plate-Preview-Metadata con JSON ASCII estricto <=2048 bytes: procedencia, región, perfil, dimensiones, transformaciones y vencimiento. CORS expondrá solo esa cabecera adicional.
**Rationale**: El resultado terminado ya contiene localización relativa y el servidor conserva original/detecciones. PNG más metadata en la misma respuesta evita desajuste entre un descriptor y una segunda descarga.
**Alternatives considered**: Descriptor JSON separado; PNG base64 en JSON; librería OpenCV adicional en navegador; nuevo trabajo persistente/endpoint para subir recortes. Son innecesarios para una región existente.
**Sources**: [FastAPI: CORS](https://fastapi.tiangolo.com/tutorial/cors/). La cabecera será tipada y validada; no incluirá texto de placa ni parámetros libres.
**Evidence**: app/domain/schemas.py, enrichment_job_service.py, enrichment_job_store.py, image_detection_store.py; frontend/src/services/apiClient.ts.

## R5. Perfil visual display-contrast-v1

**Decision**: Recortar original con geometría compartida; gris, ampliación isotrópica entera s=min(4,max(1,ceil(64/alto))), interpolación cúbica y CLAHE clipLimit=2.0, tileGridSize=8x8; PNG sin metadatos de entrada. Reducir s entero hasta cumplir límites de salida; no reducir el original por debajo de s=1. Sin padding, deskew ni perspectiva en este perfil: affine=[s,0,0,0,s,0] desde el recorte local. Si incluso s=1 excede límites o no hay región utilizable, no aplicable.
**Rationale**: Un perfil determinista de contraste/ampliación ofrece comparación geométrica sencilla; no cambia silenciosamente la lectura.
**Alternatives considered**: Enfoque agresivo, deblur, superresolución generativa, perspectiva de cuatro esquinas o deskew automático en la vista. El localizador solo entrega caja rectangular; no hay esquinas fiables. Crear píxeles interpolados no equivale a recuperar caracteres.
**Sources**: [OpenCV: CLAHE](https://docs.opencv.org/4.x/d5/daf/tutorial_py_histogram_equalization.html), [transformaciones](https://docs.opencv.org/4.x/da/d6e/tutorial_py_geometric_transformations.html). La elección es una hipótesis conservadora, no una ganancia medida.

## R6. Recursos y retirada

**Decision**: Caché solo RAM, TTL absoluto mínimo fuente/trabajo, 8 entradas y 16 MiB de PNG+metadata; entrada <=2 MiB PNG, lado <=2048, salida <=2 millones de píxeles. Un procesamiento CPU activo por proceso, cero cola; consumidores de la misma clave comparten operación y los distintos reciben 429 si no hay cupo. Deadline servidor 8 s; cliente 10 s para headers+cuerpo+decode. Permiso CPU retenido hasta terminar el hilo real, aun tras timeout. Janitor existente purga entradas <=2 s; cierre invalida todo.
**Rationale**: Son cotas de la nueva derivada, no cambios a límites de carga, modelos o umbrales. Un hilo de OpenCV puede terminar tarde: se descarta su resultado y no se permite que provoque sobreconcurrencia.
**Alternatives considered**: Un hilo por clic, cola sin límite, archivos en disco o TTL renovado por acceso. Aumentar recursos sin medir no satisface la constitución.
**Sources**: [FastAPI: concurrencia](https://fastapi.tiangolo.com/async/). El diseño combina threadpool acotado con cancelación cooperativa; no supone que cancelar HTTP detenga OpenCV.
**Evidence**: temporary_cleanup.py, inference_metrics.py y atomicidad T083. Reautorizar antes de leer, en hits y antes de publicar; al irse todos los consumidores se invalida la publicación. Cerrar sin guardar memoria sensible en archivos.

## R7. Línea base de lectura y procedencia

**Decision**: Congelar baseline-v1 como el flujo actual: lectura de crop; si ausente/confianza bajo retry_threshold, rectify_plate seguido de conservative_enhance y un segundo OCR; escoger retried solo si mayor confianza; aplicar accept_threshold vigente. La mejora actual incluye cubic max4x, gris, CLAHE y padding8; no incluye denoise. used_enhancement sigue significando intento, conservando su contrato.
**Rationale**: No es correcto vender ese reintento existente como avance de 007. Añadir provenance opcional para imágenes: policy_id, attempted_variants, selected_variant; históricos sin información se muestran como origen desconocido. No guardar textos de candidatas descartadas.
**Alternatives considered**: Inferir origen desde used_enhancement, reescribir historias previas o publicar todos los candidatos con texto.
**Evidence**: plate_quality.py, enrichment_processing.py, EnrichmentPlate y normalize_results. Video conserva la política y representación previa; el campo nuevo puede ser null/ausente.

## R8. Candidata OCR, evaluación y promoción

**Decision**: candidate-rescue-v1 es experimental/offline hasta superar SC-006. Ejecuta baseline-v1 intacta; si termina read, conserva su lectura. Solo ante unreadable evalúa como máximo dos variantes desde el crop original, nunca encadenadas: bilateral-clahe-v1 y bilateral-adaptive-v1, definidas en evaluation-protocol.md. Si candidatas aceptadas discrepan, unreadable sin texto; si coinciden, confianza de la observación ganadora, nunca sumada ni elevada. Sin candidata aceptable, conservar lectura/estado/confianza baseline, actualizando la metadata de intentos realmente ejecutados. Modelos/pesos/umbrales no cambian.
**Rationale**: La comparación debe medir aciertos y lecturas falsas sobre datos reservados, no elegir por apariencia o confianza. La política desplegada sigue baseline-v1 hasta una promoción explícita respaldada por reporte congelado; no hay auto-promoción en ejecución.
**Alternatives considered**: OCR en cada cambio de vista, aumentar umbrales/confianza, generadores de texto o probar perfiles sucesivamente sobre el conjunto reservado. Denoising puede suprimir detalle y las variantes pueden empeorar.
**Sources**: [OpenCV: filtrado](https://docs.opencv.org/4.x/d4/d13/tutorial_py_filtering.html), [umbral adaptativo](https://docs.opencv.org/4.x/d7/d4d/tutorial_py_thresholding.html).
**Dependency**: Medios autorizados y referencias verificadas, con >=60 placas reservadas; ausencia de datos bloquea acreditar exactitud, no diseñar/implementar la presentación o el evaluador. Ver evaluation-protocol.md. Sin dato real, la aceptación de US4 sigue pendiente.

## Resultado

Decisiones técnicas resueltas para Phase 1. No hay aclaraciones técnicas bloqueantes ni excepción constitucional. Los límites de rendimiento son objetivos sujetos a medición. Los pendientes externos de 006 no se trasladan ni se cierran. No se crearon dependencias de producción ni cambios de aplicación durante esta planificación.
