# Feature Specification: Extracción de características y placas

**Feature Branch**: `004-extraccion-caracteristicas-y-placas`

**Created**: 2026-11-14

**Status**: Draft

**Input**: Ampliar el backend para enriquecer detecciones vigentes de imágenes y videos con características visuales de vehículos y lectura de placas visibles, usando resultados temporales, autenticación por API key y sin interfaz frontend.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Enriquecer detecciones existentes de vehículos (Priority: P1)

Como usuario autorizado, quiero solicitar el enriquecimiento de las detecciones de vehículos de una imagen o video ya procesado para obtener características y análisis de placa sin volver a ejecutar la detección vial original.

**Why this priority**: Reutilizar detecciones ya obtenidas evita trabajo duplicado y convierte una detección general en información útil para el análisis vial.

**Independent Test**: Con un resultado temporal y vigente que contiene vehículos, el usuario crea un trabajo de enriquecimiento y consulta resultados asociados a cada detección, sin que se modifiquen ni recalculen las detecciones originales.

**Acceptance Scenarios**:

1. **Given** una imagen o video terminado, vigente y perteneciente a la API key, **When** el usuario solicita su enriquecimiento, **Then** recibe una confirmación de un trabajo temporal y puede consultar su estado y progreso.
2. **Given** varias detecciones clasificadas como vehículos, **When** termina el procesamiento, **Then** cada resultado enriquecido conserva su vínculo con la detección de origen y, en video, con el fotograma y `track_id` si existen.
3. **Given** una fuente inexistente, vencida, no terminada, sin vehículos o perteneciente a otra API key, **When** se solicita el enriquecimiento, **Then** el sistema devuelve un error seguro y no inicia un trabajo ni revela datos de la fuente.

---

### User Story 2 - Consultar características visuales (Priority: P2)

Como usuario autorizado, quiero consultar las características visuales inferidas para cada vehículo detectado para identificar los atributos que definió el modelo aprobado en la investigación.

**Why this priority**: Las características permiten usar las detecciones de vehículos como información analítica más específica que su clase general.

**Independent Test**: Con recortes controlados de vehículos y un catálogo de atributos aprobado, la consulta devuelve para cada vehículo los atributos, etiquetas y niveles de confianza producidos por el modelo.

**Acceptance Scenarios**:

1. **Given** un vehículo con un recorte válido, **When** se completa el análisis de características, **Then** el resultado publica cada atributo configurado con su etiqueta, confianza y referencia a la detección de origen.
2. **Given** un recorte inválido o un fallo de la rama de características, **When** termina el trabajo, **Then** el resultado de ese vehículo informa un estado seguro de fallo y no impide que se publiquen los resultados válidos de otros vehículos o de la rama de placa.

---

### User Story 3 - Consultar placas de forma protegida (Priority: P2)

Como usuario autorizado, quiero saber si una placa es visible, dónde fue localizada y, cuando sea legible, su texto reconocido, para complementar el análisis del vehículo sin exponer datos sensibles.

**Why this priority**: La matrícula es útil para análisis autorizado, pero es un dato sensible que requiere aislamiento y retención mínima.

**Independent Test**: Con vehículos de prueba que contienen una placa legible, una ilegible y ninguna placa visible, la consulta devuelve respectivamente los estados `read`, `unreadable` y `not_detected`, sin exponer resultados entre API keys.

**Acceptance Scenarios**:

1. **Given** una placa visible y legible en el recorte de un vehículo, **When** termina el análisis, **Then** el propietario recibe su ubicación, texto reconocido y confianza mientras el resultado temporal siga vigente.
2. **Given** que no se localiza una placa o que su texto no alcanza legibilidad suficiente, **When** termina el análisis, **Then** se publica el estado correspondiente sin inventar ni completar caracteres.
3. **Given** una API key distinta de la propietaria, **When** intenta consultar un trabajo o resultado de placa, **Then** no puede conocer su existencia ni acceder a texto, ubicación ni artefactos derivados.

---

### User Story 4 - Consultar resultados temporales y auditables (Priority: P3)

Como usuario autorizado, quiero consultar los resultados mientras estén vigentes y conocer si alguna rama no pudo completarse, para usar únicamente información verificable.

**Why this priority**: Un resultado temporal, trazable y explícito sobre sus limitaciones permite integrarlo posteriormente con una interfaz sin convertir las placas en un historial permanente.

**Independent Test**: Al simular éxito, ausencia de placa y fallo aislado en una de las ramas, la consulta conserva los resultados disponibles, comunica estados por vehículo y elimina el resultado después de su vencimiento.

**Acceptance Scenarios**:

1. **Given** que una de las dos ramas de análisis falla para un vehículo, **When** la otra termina correctamente, **Then** el resultado conserva la salida exitosa y señala el fallo sin datos internos.
2. **Given** que vence la fuente o el resultado temporal, **When** el usuario consulta o recupera un artefacto derivado, **Then** el servicio informa el vencimiento y elimina el acceso al contenido sensible.

### Edge Cases

- Una detección de vehículo tiene coordenadas fuera del marco, vacías o no permite formar un recorte válido: se informa un fallo seguro solo para esa detección.
- Una placa se localiza más de una vez en un mismo recorte: se conserva solamente la candidata de mayor confianza; no se combinan textos de varias placas.
- La placa está ocluida, desenfocada, cortada o contiene caracteres ambiguos: el resultado es `unreadable`, sin completar texto por suposición.
- Un video contiene varias observaciones del mismo `track_id`: cada resultado mantiene su fotograma de origen; no se afirma que observaciones distintas pertenezcan a una identidad real fuera del seguimiento disponible.
- La fuente temporal vence durante el procesamiento: el trabajo no publica resultados parciales ni deja artefactos recuperables.
- El análisis de características y el análisis de placa se ejecutan de forma independiente: el fallo de una rama no cancela automáticamente la otra.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST exigir una API key válida y comprobar la propiedad de la fuente antes de crear, consultar o recuperar cualquier resultado de enriquecimiento.
- **FR-002**: El sistema MUST permitir solicitar un trabajo temporal para una detección de imagen vigente o para un video terminado y vigente, reutilizando exclusivamente sus detecciones ya disponibles.
- **FR-003**: El sistema MUST seleccionar para enriquecimiento únicamente las detecciones configuradas como actores viales de tipo vehículo y formar un recorte válido, acotado al marco de la imagen o fotograma, para cada una.
- **FR-004**: El sistema MUST rechazar fuentes inexistentes, no terminadas, vencidas, no autorizadas o sin detecciones elegibles, sin exponer rutas internas, secretos ni datos de otra API key.
- **FR-005**: El sistema MUST crear un trabajo temporal con estado, progreso, vencimiento y resultados consultables para que una interfaz futura pueda integrarse sin bloquear la solicitud inicial.
- **FR-006**: El sistema MUST ejecutar en paralelo e independientemente el análisis de características y el análisis de placa para cada recorte de vehículo elegible.
- **FR-007**: El sistema MUST conservar los resultados exitosos de una rama aunque la otra rama falle, e informar por separado un estado seguro para cada rama y vehículo.
- **FR-008**: El sistema MUST publicar las características definidas por el catálogo aprobado del modelo, incluyendo nombre del atributo, etiqueta resultante, confianza y referencia a la detección de origen.
- **FR-009**: El sistema MUST localizar una placa, cuando exista, dentro del recorte del vehículo y publicar su ubicación relativa, confianza y uno de los estados `read`, `unreadable` o `not_detected`.
- **FR-010**: El sistema MUST publicar texto de matrícula y confianza de lectura únicamente cuando la placa tenga estado `read`; para los demás estados no debe fabricar, inferir ni completar caracteres.
- **FR-011**: El sistema MUST asociar cada resultado con su fuente, detección de origen y, para video, con fotograma y `track_id` cuando estén disponibles.
- **FR-012**: El sistema MUST usar los componentes aprobados para atributos, localización de placa y lectura de caracteres, y registrar de forma auditable su versión y configuración sin incluir secretos ni matrículas en los registros operativos.
- **FR-013**: El sistema MUST tratar el texto de placa, su ubicación y los recortes derivados como datos sensibles: solo la API key propietaria puede consultarlos mientras permanezcan vigentes y no deben aparecer en logs, métricas, mensajes de error ni artefactos públicos.
- **FR-014**: El sistema MUST almacenar fuentes y artefactos derivados únicamente de forma temporal, con nombres no predecibles, y eliminarlos al vencer la fuente o el trabajo; no debe crear historial permanente, exportaciones ni descargas públicas de placas.
- **FR-015**: El sistema MUST registrar de forma estructurada el identificador de solicitud, fuente, cantidad de vehículos elegibles, estado de cada rama, latencia, errores seguros y vencimiento, sin secretos, rutas internas, recortes ni texto de placas.
- **FR-016**: El sistema MUST medir y publicar internamente métricas de latencia, errores y uso de recursos por trabajo, diferenciando análisis de características y análisis de placa.
- **FR-017**: El sistema MUST documentar el contrato de creación y consulta de trabajos, estados de resultado, límites configurables y respuestas de error mediante la documentación automática de la API.

### Key Entities

- **Fuente de detección**: Resultado temporal y autorizado de una imagen o video que aporta las detecciones de vehículos ya calculadas.
- **Trabajo de enriquecimiento**: Unidad temporal asociada a una fuente y propietario, con estado, avance, vencimiento y resultados por vehículo.
- **Vehículo enriquecido**: Detección elegible con su recorte temporal y referencias a fuente, detección, fotograma y seguimiento disponibles.
- **Resultado de características**: Conjunto de atributos configurados, etiquetas y confianzas obtenidas para un vehículo.
- **Resultado de placa**: Estado de localización y legibilidad, ubicación relativa, confianza y texto únicamente cuando la lectura es válida.
- **Artefacto temporal**: Recurso derivado de la fuente que existe solo durante su periodo de vigencia y nunca es un historial permanente.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100% de solicitudes autorizadas sobre fuentes vigentes recibe la confirmación de su trabajo de enriquecimiento en un máximo de 2 segundos.
- **SC-002**: El 100% de solicitudes sobre fuentes inexistentes, vencidas, no terminadas o de otra API key se rechaza sin crear un trabajo ni exponer datos de la fuente.
- **SC-003**: En un conjunto controlado de al menos 20 recortes de vehículos, el 100% de resultados publicados conserva la referencia correcta a su detección de origen y muestra un estado independiente para características y placa.
- **SC-004**: En el mismo conjunto, el 100% de casos sin placa visible o con lectura no fiable devuelve `not_detected` o `unreadable` sin texto de matrícula inventado.
- **SC-005**: En pruebas de fallo controlado de una rama, el 100% de los resultados exitosos de la otra rama continúa disponible para el propietario autorizado.
- **SC-006**: El 100% de las pruebas entre API keys distintas impide el acceso a trabajos, resultados y placas ajenos; las pruebas de logs no contienen texto de matrícula ni rutas internas.
- **SC-007**: El 100% de trabajos y artefactos temporales vencidos deja de ser recuperable dentro del periodo de limpieza configurado.

## Assumptions

- Los modelos ya aprobados por la investigación se suministrarán mediante configuración externa: EfficientNet-B1 para características visuales, YOLOv8n para localización de placas y PaddleOCR para lectura de caracteres. Sus pesos se encuentran actualmente en `C:\Users\USER\Desktop\Mateo\Vehicle_Detection_System\weights`, pero ninguna ruta local fija formará parte del contrato desplegado.
- El catálogo de atributos, etiquetas posibles, umbrales de confianza y versiones de los componentes aprobados serán configurables y se documentarán al planificar e implementar; esta iteración no reentrena ni compara modelos.
- La matrícula completa se devuelve únicamente al propietario autenticado, durante la vigencia temporal del resultado. No se incluye una política de anonimización, exportación ni persistencia histórica en esta iteración.
- La inferencia sobre las características y la placa parte del recorte delimitado por la detección vial anterior; la iteración no ejecuta otra vez la detección general de actores viales.
- No se incluye frontend, cámara en tiempo real, reconocimiento facial, almacenamiento permanente, alertas, exportación masiva, corrección manual de OCR ni análisis de placas fuera de imágenes y videos ya procesados.
