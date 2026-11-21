# Data Model — 007

Diseño futuro. Las entidades de fuente/detección/trabajo/propietario de 006 se mantienen; no se añade una identidad de seguimiento a imágenes estáticas.

## ClassPresentation

| Campo | Regla |
|---|---|
| classKey | class_name.trim().toLowerCase(); solo presentación, no modifica identidad del DTO |
| label | Traducción del catálogo; para desconocidas, nombre recibido escapado como texto |
| color | Valor fijo del registro en frontend-interactions.md |
| known | true solo si está en el registro explícito |
| eligible | Siempre procede del servidor; jamás se infiere de color/nombre |

El registro cubre las clases por defecto y actores viales reconocidos. Una configuración que añade una clase conocida exige extender el registro/prueba. Un dato fuera del catálogo se comunica como no reconocido y neutral, sin fingir cobertura.

## SceneInteraction

- generation, sourceId, selectedDetectionId existentes; añadir focusedDetectionId y hoveredDetectionId opcionales.
- contextualDetectionId = foco válido de la fuente ?? puntero válido ?? selección válida.
- hover/leave/focus/blur solo cambian contexto. Clic/Enter/Espacio/toque explícito cambia selección; no se llama procesamiento por hover.
- Foco dentro de lista o escena cuenta; cerrar ficha limpia selección sin robar foco. En blur/leave se borra únicamente el contexto de ese control, no uno más reciente.
- Reemplazar fuente/reset/cambiar identidad/vencer borra los tres IDs y cualquier derivada. Detección sin elegibilidad: contorno no interactivo; leyenda con nombre sin ficha falsa.
- La escena usa el mismo original canónico que los crops. Anotada antigua no es un fondo de sustitución.

## PlatePreviewKey / PlatePreviewEntry

Clave: (owner_key_id, source_id, enrichment_job_id, detection_id, profile_id).
Entrada: PNG bytes + metadata juntos, coste en bytes, último acceso solo para expulsión LRU; expires_at absoluto no se renueva.

Cotas por proceso: 8 entradas y 16 MiB totales, PNG <=2 MiB por entrada, metadata ASCII <=2048 bytes, salida <=2048 por lado y <=2 Mpx. Entrada/salida RGB/gris de 8 bits; el original sigue limitado por Settings existente. No se almacena un frame decodificado completo en la caché.

Estados internos: absent -> processing -> ready; processing -> abandoned/failed/expired; ready -> evicted/expired. No hay nuevo job persistido ni endpoint de cancelación. Un miss tras expulsión puede recalcular; llamadas simultáneas de la misma clave se unen.

Un cupo de cálculo por proceso y cero cola para claves diferentes. Cada consumidor pendiente tiene token/desconexión/deadline; deadline compartido del cálculo no se amplía al unirse otro. Si todos se retiran antes de terminar, abandoned impide guardar/entregar. Si ya hubo entrega válida, ready puede retenerse hasta TTL o expulsión. El hilo tardío mantiene el cupo y descarta bytes en finally. Janitor existente y close limpian RAM; no hay residuos de disco tras reinicio.

## PlatePreviewMetadata v1

Se serializa como JSON ASCII compacto en X-Plate-Preview-Metadata. Esquema en openapi-additions.yaml.

| Campo | Validación |
|---|---|
| version | 1 |
| source_id / enrichment_job_id | Identificadores de la misma operación, no vacíos; cliente compara con su contexto |
| detection_id | Entero >=1, correspondiente al resultado/vehículo de origen |
| profile_id | display-contrast-v1; versión desconocida no se interpreta como compatible |
| input_size | width/height >=2 del recorte ORIGINAL de placa |
| output_size | width/height >=2, <=2048 y producto <=2 millones |
| original_bbox | Coordenadas enteras globales [x_min,x_max) x [y_min,y_max) del original canónico |
| applied_steps | Secuencia real: grayscale, resize_integer solo si scale>1, clahe |
| original_to_processed | Seis números finitos, matriz 2x3 local al ROI: [s,0,0,0,s,0], s entero 1..4 |
| expires_at | UTC, min(vigencia fuente,job), nunca ampliada por caché ni reintento |

input_size = diferencias de original_bbox; output_size = input_size*s. La relación describe coordenadas de borde de píxel (el muestreo interno de interpolación no inventa una nueva localización). No hay deskew/perspectiva/padding en este perfil visual. No copiar EXIF/texto o metadatos del archivo de entrada al PNG.

### Geometría y autorización

1. Resolver job por principal; completed y source_kind=image. Resolver original por mismo dueño/source ID y TTL.
2. Recuperar resultado por detection_id real, sin depender de página/posición. Verificar clase/identidad contra detección fuente, track_id null y bbox_relative válida del resultado saneado.
3. Usar caja vehicular half-open de 006. Convertir cada coordenada relativa a píxel entero truncando, corrigiendo solo error IEEE-754: nearest si abs(value-nearest)<=2*epsilon*max(1,dimensión); resto truncado. Clamp al vehículo y rechazar degeneradas.
4. ROI global = origen vehicular + ROI local; mismo cálculo que frontend/utils/imageGeometry.ts. Validar casos fraccionarios/bordes/EXIF1–8, no solo cajas enteras.
5. Read/unreadable/failed con bbox válida pueden tener preview. not_detected o sin bbox/original: no aplicable. No volver a localizar una placa para este GET.
6. Comprobar acceso y menor TTL antes de leer, en hits y antes de cachear/entregar. No cachear ni publicar después de retiro/cancelación/timeout. El servicio evita rutas de archivos como contrato.

## PlatePreviewViewState

Campos: generation, selectionKey(source+job+det+profile), status, url?, metadata?, errorCode?, view(original|processed), zoom(1|2|4), deadline monotónico.
Estados: idle -> preparing -> available | not_applicable | failed; desde cualquiera -> expired/disposed. Fallo conserva original vigente; retry repite GET de esta selección, nunca POST de inferencia.

Una operación por selectionKey. Mantener como máximo la URL procesada de la selección activa; al cambiar selección abortar consumo/decode, liberar URL/timer y descartar resultados antiguos. El original compartido sigue a cargo de lifecycle 006. Zoom y modo no forman parte de la clave ni crean llamadas.
Validar metadata/tipo/bytes/dimensiones antes de crear estado available. El presupuesto total de 10 s incluye fetch, cuerpo y decode. 401/404/410 invalidan evidencia afectada con el manejo de 006; el resto no descarta original autorizado.

## PlateReadingProvenance v1 (aditiva)

Dentro de plate, campo provenance opcional/null:

- version=1.
- policy_id: baseline-v1 | candidate-rescue-v1 | legacy-unknown.
- attempted_variants: lista única y ordenada de raw, legacy-retry-v1, bilateral-clahe-v1, bilateral-adaptive-v1; solo intentos realmente ejecutados.
- selected_variant: raw | legacy-retry-v1 | bilateral-clahe-v1 | bilateral-adaptive-v1 | none | unknown.
- Si plate.status != read: selected_variant=none salvo histórico legacy-unknown, y plate.text=null.
- Si read: selected_variant tiene que figurar en attempted_variants; unknown solo con policy legacy-unknown y lista vacía.
- No guardar textos/confianzas de candidatas descartadas. ocr_confidence conserva su escala real; para no read puede describir el mejor intento sin texto publicado.
- used_enhancement no cambia de significado: se intentó tratamiento; en la candidata será true si se intentó cualquier variante procesada, aunque no hubiera reintento legacy. Nunca derivar selected_variant desde ese booleano.
- Ausencia de provenance histórica se interpreta como desconocido, sin migración inventada. Nuevos trabajos de imagen producen metadata exacta, incluidos fallos antes/durante OCR.
- Video conserva flujo anterior, admite campo null/ausente y no activa candidatas.

Validar y sanear antes de results_json, tablas normalizadas/respuestas. El campo aditivo vive en JSON temporal existente; no requiere tabla de variantes ni almacén de textos. Mantener reglas de finish/TTL/cancelación y desenlace atómico de T083.

## EvaluationRun

run_id privado, split/group IDs pseudónimos, hash del manifiesto/reglas/perfiles, versiones de dependencias/modelos/pesos, umbrales, hardware, concurrencia, conteos y costes. Textos/imágenes/rutas de referencia solo en manifiesto privado autorizado; informe compartible solo agregado. Modelar attempted vs selected de forma idéntica a producción. Ver evaluation-protocol.md.
