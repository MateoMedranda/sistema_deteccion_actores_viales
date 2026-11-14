# Feature Specification: Interfaz web prototipo vial

**Feature Branch**: `005-interfaz-web-prototipo-vial`
**Created**: 2026-11-14
**Status**: Draft
**Input**: Construir una interfaz web inicial, sencilla y funcional para demostrar de forma visual el comportamiento de todas las capacidades disponibles del sistema vial.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Analizar una imagen vial (Priority: P1)

Como usuario de demostración, quiero cargar una imagen y ver las detecciones y el resultado anotado para comprobar que el análisis funciona de extremo a extremo.

**Why this priority**: Es la forma más rápida de validar visualmente el sistema base sin conocer herramientas de API.

**Independent Test**: Una persona ingresa una credencial válida, selecciona una imagen permitida, inicia el análisis y ve el estado, las detecciones y la imagen anotada o un mensaje seguro de error.

**Acceptance Scenarios**:

1. **Given** una imagen válida y una credencial configurada por el usuario, **When** inicia el análisis, **Then** la interfaz muestra una confirmación mientras espera y presenta la imagen anotada, clase, confianza y caja de cada detección al terminar.
2. **Given** un archivo inválido, demasiado grande o un servicio no disponible, **When** intenta analizarlo, **Then** la interfaz comunica el error de manera comprensible sin mostrar secretos, rutas internas ni detalles técnicos.

---

### User Story 2 - Procesar y explorar un video (Priority: P1)

Como usuario de demostración, quiero cargar un video y seguir su trabajo hasta ver el video anotado, detecciones y resumen para comprobar el procesamiento asíncrono.

**Why this priority**: El procesamiento de video, seguimiento y resultados temporales son parte central del prototipo final.

**Independent Test**: Con un video aceptado, la interfaz conserva su identificador temporal, actualiza el estado hasta terminar y permite consultar el resultado mientras siga vigente.

**Acceptance Scenarios**:

1. **Given** un video válido, **When** se envía, **Then** se muestran el estado, progreso y mensajes de fallo o cancelación del trabajo.
2. **Given** un video terminado, **When** se consulta su resultado, **Then** se visualizan el video anotado, resumen por clase y una lista paginable de detecciones sin revelar datos internos.

---

### User Story 3 - Configurar y observar conteo por línea (Priority: P1)

Como usuario de demostración, quiero dibujar una línea sobre el video terminado y observar sus conteos para verificar los cruces por clase y sentido.

**Why this priority**: La configuración visual elimina la necesidad de calcular manualmente coordenadas y demuestra la funcionalidad de conteo.

**Independent Test**: Sobre un video terminado, el usuario marca dos puntos con el mouse, inicia el conteo y ve la línea, el avance y los totales por clase/dirección.

**Acceptance Scenarios**:

1. **Given** un video con dimensiones conocidas, **When** el usuario arrastra dos extremos sobre su vista, **Then** la interfaz convierte los puntos a coordenadas normalizadas y permite confirmar o reajustar la línea.
2. **Given** un trabajo de conteo aceptado, **When** progresa o termina, **Then** la interfaz muestra su estado, eventos y resumen por clase y sentido; si falla, muestra un error seguro.

---

### User Story 4 - Consultar atributos y placas protegidos (Priority: P2)

Como usuario autorizado, quiero solicitar el enriquecimiento de una imagen o video ya procesado y ver atributos y estados de placa para comprobar esa capacidad sin crear un historial visible.

**Why this priority**: Permite observar el flujo integral de atributos y placas, respetando las restricciones de datos sensibles.

**Independent Test**: El usuario crea un enriquecimiento sobre una fuente vigente propia, consulta su avance y visualiza atributos, estado de placa, confianza y texto solo cuando el backend lo autoriza.

**Acceptance Scenarios**:

1. **Given** una fuente propia vigente, **When** se solicita el enriquecimiento, **Then** la interfaz muestra el estado y resultados por vehículo o `track_id` cuando estén disponibles.
2. **Given** una placa no leída, ausente o un trabajo vencido, **When** se presentan los resultados, **Then** la interfaz muestra únicamente el estado seguro; no conserva, exporta ni muestra texto de placa inexistente.

---

### Edge Cases

- La credencial es ausente, inválida o se reemplaza durante una sesión.
- Un trabajo expira, es cancelado o falla mientras se está consultando.
- El usuario intenta contar antes de que el video esté terminado o dibuja una línea de longitud cero.
- La ventana se redimensiona tras dibujar la línea: la selección conserva su posición normalizada.
- El resultado contiene cero detecciones, cero eventos, atributos fallidos o una placa sin lectura.
- El backend de enriquecimiento no está listo por falta de modelos: la interfaz conserva las funciones disponibles y comunica el estado sin bloquear la demostración de imagen, video o conteo.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: La interfaz MUST permitir que el usuario configure una credencial de acceso para la sesión y la use en cada operación protegida, sin incluirla en enlaces, capturas de errores, almacenamiento permanente ni código publicado.
- **FR-002**: La interfaz MUST permitir seleccionar y enviar una imagen, mostrar el avance visible de la solicitud y presentar el resultado anotado junto con detecciones legibles.
- **FR-003**: La interfaz MUST permitir seleccionar y enviar un video, conservar su identificador temporal durante la sesión y consultar periódicamente su estado hasta un estado terminal o vencimiento.
- **FR-004**: La interfaz MUST mostrar el video anotado y los resultados temporales disponibles de un video terminado, incluyendo resumen y detecciones con navegación paginada cuando aplique.
- **FR-005**: La interfaz MUST permitir dibujar, ajustar y borrar una línea usando dos puntos sobre la representación del video y convertirla proporcionalmente a las dimensiones originales antes de solicitar el conteo.
- **FR-006**: La interfaz MUST mostrar el estado, avance, eventos y totales de un conteo por línea, diferenciando clase y sentido de cruce.
- **FR-007**: La interfaz MUST permitir crear y consultar un trabajo de enriquecimiento sobre una imagen o video propio vigente y mostrar atributos, evidencias no sensibles, estados de placa y texto únicamente cuando el backend lo entregue como legible.
- **FR-008**: La interfaz MUST representar de forma segura los estados `queued`, `processing`, `completed`, `failed`, `cancelled`, `expired`, `read`, `unreadable` y `not_detected`, sin sustituir información del backend por inferencias propias.
- **FR-009**: La interfaz MUST ofrecer mensajes claros para validación, errores de autorización, no disponibilidad, conflicto y vencimiento, sin exponer contenido técnico sensible.
- **FR-010**: La interfaz MUST permitir reiniciar una demostración y eliminar del estado visible los identificadores, archivos seleccionados, resultados y texto de placa de la sesión actual.
- **FR-011**: La interfaz MUST documentar cómo configurarla, iniciarla y vincularla con el servicio local, incluyendo las funcionalidades que pueden no estar disponibles mientras los modelos estén en mantenimiento.
- **FR-012**: La interfaz MUST mantener módulos separados para carga, estado de trabajos, visualización de resultados, dibujo de línea y acceso al servicio, de modo que otro integrante pueda mejorar su diseño o sustituir una sección sin reescribir el prototipo completo.

### Key Entities

- **Sesión de demostración**: Estado local y efímero de credencial, fuente seleccionada, identificadores temporales y resultados visibles.
- **Fuente de análisis**: Imagen o video enviado por el usuario y su identificador temporal de consulta.
- **Trabajo**: Operación temporal de video, conteo o enriquecimiento que expone estado, avance, vencimiento y resultado.
- **Línea de conteo**: Dos puntos normalizados, configurables visualmente, asociados a un video terminado.
- **Resultado enriquecido**: Atributos de vehículo y estado de placa pertenecientes a una fuente temporal y accesibles solo al propietario.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En una demostración local con el servicio disponible, el usuario completa el análisis de una imagen y visualiza su resultado en menos de 2 minutos desde abrir la interfaz.
- **SC-002**: El 100% de los trabajos iniciados desde la interfaz muestra un estado comprensible y finaliza en resultado, error, cancelación o vencimiento sin dejar la pantalla bloqueada.
- **SC-003**: El 100% de líneas dibujadas y confirmadas conserva sus dos extremos dentro del video al redimensionar la pantalla y genera coordenadas normalizadas válidas.
- **SC-004**: El 100% de respuestas de autorización, validación, conflicto, indisponibilidad o vencimiento se comunica sin revelar credenciales, rutas internas ni texto de placa no autorizado.
- **SC-005**: Una persona que no conoce la API puede completar los flujos de imagen, video y conteo usando únicamente la interfaz y la guía de inicio.
- **SC-006**: Los resultados de placa y los identificadores de trabajos desaparecen de la vista al reiniciar la demostración o al cerrar la sesión de navegación.

## Assumptions

- La interfaz se utilizará localmente como demostrador académico y no sustituye una aplicación de producción.
- El backend existente mantiene sus contratos y documentación de consulta; la interfaz no duplica algoritmos de detección, seguimiento, conteo ni OCR.
- La credencial es introducida conscientemente por el usuario para la sesión actual y solo se conserva en memoria durante la demostración.
- La primera versión prioriza claridad funcional sobre identidad visual, accesibilidad avanzada, cuentas de usuario, persistencia de preferencias, optimización para móvil o diseño final.
- La demostración de enriquecimiento puede informar que no está disponible mientras se completa la configuración de modelos del backend.
