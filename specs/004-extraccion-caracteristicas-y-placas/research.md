# Research: Extracción de características y placas

## Decisión 1: Crear un trabajo temporal de enriquecimiento independiente

**Decision**: Crear `EnrichmentJob` con la misma máquina de estados de los trabajos de video y conteo: `queued`, `processing`, `completed`, `failed` y `cancelled`.

**Rationale**: El enriquecimiento de un video puede involucrar múltiples vehículos y ramas de inferencia. Una respuesta asíncrona permite confirmar la solicitud en menos de dos segundos, mostrar progreso y cancelar/expirar de forma segura.

**Alternatives considered**:

- Ejecutar el enriquecimiento dentro de la solicitud HTTP: se rechaza porque bloquea la API y no escala a videos.
- Reutilizar el trabajo de video como si fuera el de enriquecimiento: se rechaza porque mezcla detección base, errores y TTL de resultados distintos.

## Decisión 2: Retener de forma privada la fuente necesaria para los recortes

**Decision**: Guardar una copia temporal y privada de la imagen original y sus detecciones con propietario; conservar el archivo de entrada del video terminado hasta que expire el `VideoJob`. El vencimiento del enriquecimiento será `min(expires_at_de_la_fuente, ENRICHMENT_RESULT_TTL_SECONDS)`.

**Rationale**: Las detecciones existentes contienen cajas, pero el servicio actual solo conserva la imagen anotada y elimina la entrada del video después de procesarlo. Una caja sin píxeles no permite extraer atributos ni placa. La copia temporal con ruta aleatoria permite generar recortes sin volver a detectar actores.

**Alternatives considered**:

- Ejecutar el detector vial base otra vez: se rechaza porque contradice FR-002 y aumenta costo/latencia.
- Guardar recortes permanentemente: se rechaza porque contradice minimización y retención limitada de datos sensibles.
- Usar la imagen anotada como fuente: las cajas/etiquetas alteran píxeles y no es el original confiable.

## Decisión 3: Adaptadores tipados y carga única de modelos

**Decision**: Definir contratos `AttributeExtractor`, `PlateLocalizer`, `PlateReader` y `PlatePreprocessor`; cargar EfficientNet-B1, YOLOv8n de placas y PaddleOCR una sola vez durante el ciclo de vida de la aplicación.

**Rationale**: Mantiene las rutas independientes de pesos, facilita mocks y evita inicialización por solicitud. El checkpoint de EfficientNet-B1 requiere un manifiesto externo con arquitectura, etiquetas, tamaño, orden de color, normalización, umbrales y checksum; no se deben suponer etiquetas ni transformaciones genéricas.

**Alternatives considered**:

- Llamar a cada biblioteca desde la ruta: se rechaza por acoplamiento, pruebas difíciles y cargas repetidas.
- Inferir la configuración del EfficientNet solo desde el nombre del archivo: se rechaza porque un checkpoint personalizado puede tener cabeza, etiquetas y normalización distintas.

## Decisión 4: Paralelismo con límites y aislamiento por modelo

**Decision**: Un trabajador toma cada `EnrichmentJob`; sus ramas de atributos y placa se programan independientemente con semáforos/colas configurables por modelo. El valor inicial permite una rama de atributos y una de placa por unidad, sin ejecutar más trabajos de enriquecimiento simultáneos que `MAX_CONCURRENT_ENRICHMENT_JOBS`.

**Rationale**: Cumple FR-006 sin crear concurrencia ilimitada ni agotar la GPU. Si un adaptador no es seguro para múltiples llamadas, su semáforo se fija en uno sin cambiar el contrato de la rama.

**Alternatives considered**:

- Paralelismo ilimitado por caja/fotograma: se rechaza por riesgo de OOM y pérdida de estabilidad.
- Ejecución estrictamente secuencial: se rechaza porque contradice el procesamiento independiente solicitado.

## Decisión 5: Lectura de placa basada en evidencia, no en texto inventado

**Decision**: Para una placa localizada, ejecutar OCR sobre el recorte original. Si la confianza está bajo `PLATE_OCR_RETRY_THRESHOLD`, aplicar rectificación de perspectiva/orientación y variantes conservadoras de contraste, reducción de ruido, nitidez y escalado, seguido de un único reintento. Aceptar texto solo si alcanza `PLATE_OCR_ACCEPT_THRESHOLD`; las reglas de formato validan o rechazan, nunca corrigen caracteres.

**Rationale**: El OCR entrega una puntuación de reconocimiento que puede actuar como puerta de aceptación. La mejora generativa tipo “HD” se excluye porque puede alucinar trazos; la salida `unreadable` es preferible a una matrícula falsa.

**Alternatives considered**:

- Mejorar todas las placas: se rechaza por consumo adicional y porque puede degradar recortes ya buenos.
- Corregir texto mediante regex: se rechaza porque puede convertir una observación errónea en un identificador falso.
- No reintentar: se rechaza porque no aprovecha evidencia válida de baja calidad.

## Decisión 6: Consolidar resultados de video por `track_id`

**Decision**: Agrupar observaciones de vehículo por `track_id`, tomar un máximo configurable de candidatos de mejor calidad por track y devolver un único resultado consolidado. Los atributos escogen la observación más confiable; la placa acepta una lectura solo si existe consenso ponderado por calidad, localización y confianza OCR. Si no hay consenso suficiente, el estado es `unreadable`.

**Rationale**: Reduce duplicados, exposición de placas y costo sin afirmar que el track identifica a una persona o vehículo real fuera del video.

**Alternatives considered**:

- Un resultado por fotograma: se rechaza por volumen, duplicados y exposición innecesaria.
- Escoger siempre el último fotograma: se rechaza porque no garantiza enfoque, tamaño ni visibilidad.

## Decisión 7: Observabilidad y evidencia de calidad protegidas

**Decision**: Registrar solo identificadores, contadores, estados, latencias, memoria y versiones/checksums no secretos. Medir atributos por etiqueta (macro F1), localización de placas (AP/IoU), OCR (exactitud de placa y CER), tasa de lectura falsa y diferencias entre original, reintento y consenso.

**Rationale**: La constitución exige evidencia reproducible sin filtrar texto de placas, recortes ni rutas internas.

**Alternatives considered**:

- Registrar texto OCR para depurar: se rechaza porque expone un dato sensible.
- Declarar calidad solo por confianza interna: se rechaza porque la confianza no reemplaza una evaluación con verdad de referencia.

## Dependencias y compatibilidad

- Declarar de manera explícita las dependencias de PaddleOCR/PaddlePaddle y el cargador de EfficientNet-B1, con versiones compatibles con Python 3.12 y el dispositivo configurado. Ejecutar smoke test antes de habilitar `ready`.
- Configurar externamente: pesos, manifiesto de atributos, directorio/modelo OCR, idioma, dispositivo, umbrales, lista de clases vehiculares, TTL, rutas privadas, concurrencia y máximo de candidatos por track.
- Los pesos locales indicados por el usuario son un insumo de desarrollo; sus rutas no se incorporan a código ni a contratos desplegados.

## Fuentes técnicas

- [Torchvision: EfficientNet-B1 y sus transformaciones/metadata](https://docs.pytorch.org/vision/2.0/models/generated/torchvision.models.efficientnet_b1.html)
- [Ultralytics: parámetros de predicción y confianza](https://docs.ultralytics.com/modes/predict/)
- [PaddleOCR: reconocimiento, `rec_score` y umbrales](https://paddlepaddle.github.io/PaddleOCR/main/en/version3.x/pipeline_usage/OCR.html)
