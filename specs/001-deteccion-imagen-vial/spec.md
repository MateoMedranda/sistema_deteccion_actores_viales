# Feature Specification: Detección vial en imagen

**Feature Branch**: `001-deteccion-imagen-vial`

**Created**: 2026-10-21

**Status**: Draft

**Input**: Usuario solicita analizar una imagen de actores viales y obtener resultados estructurados
y una visualización de las detecciones.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Analizar una imagen vial (Priority: P1)

Como usuario de una interfaz cliente, quiero enviar una imagen de una vía y recibir las detecciones
de actores viales para identificar qué objetos reconoce el sistema y dónde se encuentran.

**Why this priority**: Es el valor mínimo de la primera iteración; demuestra que el modelo aprobado
puede ser utilizado por una interfaz cliente de manera confiable.

**Independent Test**: Se envía una imagen de prueba válida que contiene actores viales y se verifica
que el usuario recibe un resultado estructurado y una imagen anotada que permiten interpretar cada
detección sin consultar información adicional.

**Acceptance Scenarios**:

1. **Given** una imagen vial válida con actores reconocibles, **When** el usuario solicita el
   análisis, **Then** recibe una lista de detecciones con clase, confianza y ubicación de cada actor.
2. **Given** una imagen vial válida con al menos una detección, **When** finaliza el análisis,
   **Then** el usuario puede visualizar la misma imagen con cajas, clase y nivel de confianza para
   cada detección.
3. **Given** una imagen válida sin actores que alcancen el criterio de detección, **When** se la
   analiza, **Then** el usuario recibe un resultado exitoso sin detecciones y una indicación clara
   de que no se encontraron actores viales.

---

### User Story 2 - Recibir orientación ante una carga inválida (Priority: P2)

Como usuario, quiero recibir un mensaje claro cuando mi imagen no se pueda analizar para corregir
la carga sin poner en riesgo la información del sistema.

**Why this priority**: Evita procesamientos inseguros o fallidos y permite al usuario resolver el
problema por sí mismo.

**Independent Test**: Se intentan enviar archivos con formato no permitido, contenido corrupto y
tamaño mayor al límite configurado; cada caso comunica el motivo de rechazo sin revelar detalles
internos.

**Acceptance Scenarios**:

1. **Given** un archivo que no es una imagen permitida, **When** el usuario intenta enviarlo,
   **Then** el sistema lo rechaza y explica que debe seleccionar una imagen compatible.
2. **Given** una imagen corrupta o que supera el límite permitido, **When** el usuario intenta
   analizarla, **Then** el sistema la rechaza con un mensaje seguro y no genera resultados parciales.

---

### User Story 3 - Consumir resultados desde una interfaz cliente (Priority: P3)

Como responsable de una interfaz cliente, quiero disponer de un resultado estable y documentado
para mostrar el análisis a los usuarios sin interpretar datos internos del sistema.

**Why this priority**: Permite integrar la capacidad de detección con una interfaz web futura sin
ampliar el alcance de esta iteración hacia la construcción de dicha interfaz.

**Independent Test**: Una interfaz de prueba consume un resultado de ejemplo y muestra los campos
de detección y la visualización anotada sin transformación manual ni acceso a información interna.

**Acceptance Scenarios**:

1. **Given** una solicitud de análisis completada, **When** una interfaz cliente consulta el
   resultado, **Then** puede mostrar las detecciones y la visualización anotada con los datos
   publicados y documentados.

### Edge Cases

- La imagen contiene objetos muy pequeños, parcialmente ocultos o con iluminación deficiente: el
  resultado conserva solamente las detecciones que cumplan el criterio aprobado y comunica la
  ausencia de detecciones cuando corresponda.
- La imagen tiene orientación inusual, dimensiones extremas o canales no compatibles: se normaliza
  de forma segura o se rechaza con un mensaje claro antes del análisis.
- Varias solicitudes llegan al mismo tiempo: cada usuario recibe únicamente el resultado asociado a
  su solicitud, sin mezclar imágenes ni detecciones.
- El modelo no está disponible temporalmente: el usuario recibe una respuesta segura que indica que
  el análisis no pudo completarse y puede reintentar más tarde.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST permitir a usuarios autorizados enviar una única imagen para su
  análisis de actores viales.
- **FR-002**: El sistema MUST validar que la carga sea una imagen permitida, íntegra, dentro de los
  límites configurados y apta para ser analizada antes de procesarla.
- **FR-003**: El sistema MUST analizar cada imagen válida con el modelo de detección aprobado para
  la investigación del proyecto.
- **FR-004**: El sistema MUST devolver por cada detección la clase de actor vial, el nivel de
  confianza y la ubicación dentro de la imagen.
- **FR-005**: El sistema MUST proporcionar una representación visual anotada de la imagen analizada
  con una caja, clase y confianza para cada detección devuelta.
- **FR-006**: El sistema MUST informar de manera clara y segura los rechazos de carga, fallos de
  análisis y falta temporal de disponibilidad, sin exponer secretos, rutas internas ni detalles
  sensibles.
- **FR-007**: El sistema MUST publicar un contrato de resultados documentado y estable para que una
  interfaz cliente pueda presentar las detecciones y la visualización anotada.
- **FR-008**: El sistema MUST registrar, para fines operativos, el resultado de la solicitud, el
  tiempo total de análisis y los errores, sin registrar secretos ni conservar innecesariamente la
  imagen original.
- **FR-009**: El sistema MUST eliminar las cargas y resultados temporales cuando dejen de ser
  necesarios para entregar la respuesta; esta iteración no mantiene un historial de análisis.
- **FR-010**: El sistema MUST mantener disponible la capacidad de análisis para solicitudes válidas
  consecutivas sin requerir intervención manual entre solicitudes.

### Key Entities

- **Solicitud de análisis**: Petición identificable de un usuario autorizado para analizar una sola
  imagen; incluye el estado, momento de recepción y resultado operativo.
- **Imagen enviada**: Archivo visual temporal proporcionado por el usuario y validado antes de su
  análisis; no forma parte de un historial persistente en esta iteración.
- **Detección vial**: Resultado individual que representa un actor vial reconocido, su clase, nivel
  de confianza y ubicación dentro de la imagen.
- **Visualización anotada**: Representación de la imagen original con las detecciones superpuestas
  para facilitar su interpretación por el usuario.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Al menos el 95% de las imágenes válidas del conjunto de prueba de referencia se
  completan y entregan sus resultados al usuario en cinco segundos o menos, bajo el entorno de
  medición documentado.
- **SC-002**: El 100% de los casos de prueba con archivos no permitidos, corruptos o que superen el
  límite configurado se rechazan antes de iniciar el análisis y muestran una explicación segura.
- **SC-003**: El 100% de las detecciones devueltas en el conjunto de prueba incluye clase,
  confianza, ubicación y una visualización anotada correspondiente.
- **SC-004**: Una interfaz cliente de prueba puede mostrar los resultados de al menos 20 imágenes de
  referencia usando exclusivamente el contrato publicado, sin requerir acceso a datos internos.
- **SC-005**: Durante una prueba de 20 solicitudes válidas consecutivas, ninguna respuesta mezcla
  resultados, imágenes o datos de otra solicitud.

## Assumptions

- El modelo seleccionado, sus etiquetas de actores viales y los criterios de confianza aprobados
  están disponibles antes de comenzar la planificación técnica.
- Las personas que usen esta primera iteración cuentan con autorización para analizar las imágenes
  enviadas y las imágenes no contienen material fuera de los permisos del proyecto.
- El límite exacto de tamaño de carga y los formatos permitidos se definirán como configuración
  documentada durante la planificación, sin cambiar los criterios funcionales de esta especificación.
- La primera iteración se limitará a una imagen por solicitud. Videos, cámara en tiempo real,
  extracción o almacenamiento de placas, historial persistente e interfaz web completa se abordarán
  en iteraciones posteriores.
- La representación visual anotada estará disponible para que la interfaz cliente la muestre, pero
  el desarrollo de una interfaz web de producción no es parte de esta funcionalidad.
