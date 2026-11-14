# Feature Specification: Procesamiento vial por video

**Feature Branch**: `002-procesamiento-video-vial`

**Created**: 2026-11-12

**Status**: Draft

**Input**: Ampliar el servicio existente para aceptar videos viales, validarlos y procesarlos como
trabajos asíncronos, reutilizando de forma segura los contratos y componentes de la iteración 001.

## Clarifications

### Session 2026-11-12

- Q: ¿Qué perfil máximo de video debe aceptar esta iteración? → A: MP4 con H.264; hasta 100 MB, 2 minutos, 1080p, 30 fps y 3600 fotogramas.
- Q: ¿Qué garantía de continuidad deben tener los trabajos si el servicio se reinicia durante el procesamiento? → A: Cola temporal persistente; los trabajos pendientes se reanudan hasta su expiración.
- Q: ¿Cómo debe entregarse el detalle de detecciones de un video terminado? → A: Resultado principal con resumen y video anotado; detecciones por fotograma mediante consulta paginada.
- Q: ¿Cuánto tiempo deben conservarse temporalmente los videos y resultados de un trabajo terminado? → A: Original eliminado al terminar; resultado anotado y metadatos disponibles 60 minutos.
- Q: ¿Qué enfoque de rastreo debe usarse para mantener el mismo track_id entre fotogramas? → A: ByteTrack; BoT-SORT queda como alternativa para una prueba comparativa futura.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Enviar un video vial para análisis (Priority: P1)

Como usuario autorizado, quiero enviar un video vial válido y recibir la confirmación de un trabajo
para poder continuar sin esperar a que termine el análisis.

**Why this priority**: Es la capacidad mínima que convierte la detección de una imagen en
procesamiento de video sin bloquear al usuario durante todo el análisis.

**Independent Test**: Un usuario autorizado envía un video controlado válido y recibe un
identificador de trabajo y estado inicial; un archivo no válido es rechazado antes de crear un
trabajo.

**Acceptance Scenarios**:

1. **Given** un usuario autorizado y un video vial dentro de los límites configurados, **When** lo
   envía para análisis, **Then** recibe una confirmación con un identificador único y el estado
   `queued` sin tener que esperar el resultado.
2. **Given** un video con formato, duración, códec, resolución o tamaño no permitido, **When** el
   usuario intenta enviarlo, **Then** recibe un error claro y seguro y no se crea un trabajo ni un
   resultado temporal.
3. **Given** que la capacidad de procesamiento alcanzó su límite configurado, **When** el usuario
   envía un video válido, **Then** el trabajo queda en espera o recibe una respuesta segura según
   la política configurada, sin mezclarlo con otro trabajo.
4. **Given** un reinicio del servicio antes de que expire un trabajo pendiente, **When** el
   servicio vuelve a estar disponible, **Then** el trabajo conserva su estado temporal y continúa
   o se reanuda sin publicar resultados de otro trabajo.

---

### User Story 2 - Consultar y cancelar un trabajo de video (Priority: P2)

Como usuario autorizado, quiero consultar el avance, el estado final y, cuando sea necesario,
cancelar mi trabajo para controlar el procesamiento de mi video.

**Why this priority**: Los videos requieren más tiempo que una imagen; el usuario necesita
visibilidad y control sin acceder a detalles internos del servicio.

**Independent Test**: Se crea un trabajo con un video de prueba y se consulta su estado durante y
después del procesamiento; se cancela un trabajo en espera y se verifica que no se publica un
resultado.

**Acceptance Scenarios**:

1. **Given** un trabajo en espera o en procesamiento, **When** el usuario consulta su
   identificador, **Then** recibe su estado, avance y datos públicos de progreso.
2. **Given** un trabajo terminado, **When** el usuario consulta su identificador, **Then** recibe
   el resumen de detecciones y una referencia temporal al video anotado.
3. **Given** un trabajo terminado con muchas detecciones, **When** el usuario solicita el detalle
   por fotograma, **Then** lo recibe en partes paginadas usando únicamente datos públicos del
   trabajo.
4. **Given** un trabajo en espera o en procesamiento, **When** su propietario solicita
   cancelarlo, **Then** el trabajo pasa a `cancelled` de forma segura y no queda un video anotado
   accesible.
5. **Given** un identificador inexistente, vencido o perteneciente a otra credencial, **When** se
   consulta o cancela, **Then** el servicio responde sin revelar datos de otro trabajo.

---

### User Story 3 - Revisar actores rastreados en un video terminado (Priority: P3)

Como usuario autorizado, quiero obtener un video anotado y un resumen de actores por clase con
identificadores de seguimiento persistentes para interpretar cómo aparecen y se desplazan los
actores viales durante el video.

**Why this priority**: Aporta el valor analítico propio del video y prepara las iteraciones futuras
de conteo sin incorporar todavía conteo por línea ni una interfaz gráfica.

**Independent Test**: Se procesa un video controlado con actores viales y se comprueba que las
detecciones de un mismo actor conservan el mismo identificador de seguimiento entre fotogramas
consecutivos y que el resumen coincide con los resultados publicados.

**Acceptance Scenarios**:

1. **Given** un video terminado con actores detectables, **When** el usuario consulta el
   resultado, **Then** cada detección publicada contiene clase, confianza, ubicación, número de
   fotograma y `track_id`.
2. **Given** un actor que permanece visible en fotogramas consecutivos, **When** el trabajo
   termina, **Then** el actor conserva un `track_id` estable mientras el seguimiento sea posible.
3. **Given** un trabajo terminado, **When** el usuario obtiene el video anotado, **Then** cada
   actor detectado se muestra con caja, clase, confianza e identificador de seguimiento, y el
   resumen por clase concuerda con los datos publicados.

### Edge Cases

- El archivo declara un formato permitido pero está corrupto, no contiene secuencia de video o usa
  un códec no admitido: se rechaza antes de crear el trabajo.
- El video excede alguno de los límites configurados de tamaño, duración, resolución o número de
  fotogramas: se rechaza antes de iniciar inferencia.
- El modelo deja de estar disponible durante un trabajo: el trabajo pasa a `failed` con un código
  público seguro y se limpian sus resultados parciales.
- El servicio se reinicia mientras existen trabajos no vencidos: los estados y la cola temporal se
  recuperan y el procesamiento se reanuda de manera aislada.
- Se solicita cancelar mientras se procesa un fotograma: la cancelación se aplica antes del
  siguiente fotograma seguro, sin publicar un artefacto parcial.
- Un trabajo ya terminado o fallido recibe una cancelación: se conserva su estado terminal y se
  informa un resultado consistente.
- El video anotado expira: su referencia deja de ser accesible sin conservar un historial
  permanente. El resultado anotado y sus metadatos expiran a los 60 minutos de terminar el
  trabajo.
- Varios trabajos son enviados a la vez: el límite de concurrencia evita la sobrecarga y cada
  avance, resultado y artefacto permanece asociado exclusivamente con su propio trabajo.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST permitir que un usuario autorizado envíe un solo video vial por
  solicitud y reciba una confirmación asíncrona con identificador único de trabajo.
- **FR-002**: El sistema MUST autenticar y autorizar al solicitante antes de aceptar o almacenar el
  contenido del video y debe reutilizar el formato seguro de errores de la iteración 001.
- **FR-003**: El sistema MUST validar antes de crear un trabajo el tipo declarado, extensión,
  decodificación, códec, tamaño, duración, resolución y número de fotogramas del video. El perfil
  inicial aceptado es MP4 con H.264, hasta 100 MB, 2 minutos, 1920×1080, 30 fps y 3600 fotogramas;
  sus límites deben permanecer configurables.
- **FR-004**: El sistema MUST representar cada trabajo mediante los estados `queued`,
  `processing`, `completed`, `failed` y `cancelled`, publicar solamente transiciones válidas y
  conservar temporalmente los trabajos no vencidos para reanudar los pendientes tras un reinicio.
- **FR-005**: El sistema MUST permitir consultar a un usuario autorizado el estado, porcentaje de
  avance, información temporal y resultado público de su propio trabajo.
- **FR-006**: El sistema MUST procesar los fotogramas de un trabajo válido con el modelo aprobado,
  reutilizado desde la carga del servicio, sin reinicializarlo por trabajo ni por fotograma.
- **FR-007**: El sistema MUST usar ByteTrack para asignar y conservar un `track_id` para cada actor
  mientras su seguimiento entre fotogramas consecutivos sea posible, sin prometer continuidad tras
  una oclusión o salida de escena.
- **FR-008**: El sistema MUST producir para cada trabajo completado un resumen de detecciones por
  clase y publicar su detalle por fotograma de forma paginada, con clase, confianza, ubicación,
  número de fotograma y `track_id`.
- **FR-009**: El sistema MUST generar un video anotado temporal que muestre las cajas, clases,
  confianzas e identificadores de seguimiento de las detecciones publicadas.
- **FR-010**: El sistema MUST permitir cancelar un trabajo en espera o en procesamiento; la
  cancelación debe impedir la publicación de nuevos resultados y limpiar los artefactos parciales.
- **FR-011**: El sistema MUST aplicar un límite configurable de concurrencia y un tiempo máximo de
  procesamiento, y comunicar de forma segura la saturación, el vencimiento o un fallo.
- **FR-012**: El sistema MUST registrar de forma estructurada el identificador de trabajo, estado,
  avance, tiempos por video y fotograma, uso de memoria, errores y resultado, sin registrar
  secretos, rutas internas ni contenido sensible.
- **FR-013**: El sistema MUST conservar el video de entrada solo mientras el trabajo lo necesita y
  eliminarlo al completar, cancelar o fallar. El video anotado y los metadatos públicos de un
  trabajo completado deben expirar y eliminarse automáticamente 60 minutos después de terminar.
- **FR-014**: El sistema MUST publicar un contrato documentado y versionado para carga, consulta,
  cancelación y recuperación temporal de resultados, compatible con los patrones públicos de la
  iteración 001.

### Key Entities

- **Trabajo de video**: Unidad temporal identificada que representa un video enviado, su
  propietario autorizado, estado, progreso, tiempos y código público de error cuando corresponda.
- **Video validado**: Archivo temporal cuyo tipo, integridad, códec, tamaño, duración, resolución y
  cantidad de fotogramas fueron aceptados antes de procesarlo.
- **Detección por fotograma**: Resultado de un actor vial en un fotograma, con clase, confianza,
  ubicación, índice de fotograma y `track_id`.
- **Seguimiento de actor**: Asociación temporal que relaciona detecciones de un mismo actor entre
  fotogramas consecutivos mediante un `track_id`.
- **Resumen de detecciones**: Agregado por clase de las detecciones y seguimientos publicados para
  un trabajo terminado.
- **Página de detecciones**: Parte ordenada y limitada del detalle por fotograma de un trabajo
  terminado, accesible solo mediante información pública y autorización válida.
- **Video anotado temporal**: Resultado visual de duración limitada que incluye las anotaciones
  publicadas y se asocia exclusivamente con un trabajo completado.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100% de las cargas válidas dentro de los límites configurados reciben una
  confirmación de trabajo en un máximo de 2 segundos, sin esperar la finalización del análisis.
- **SC-002**: El 100% de los videos con tipo, extensión, códec, tamaño, duración o resolución no
  permitidos se rechazan antes de crear un trabajo o iniciar el análisis y reciben un mensaje
  seguro.
- **SC-003**: Al menos el 95% de un conjunto documentado de 20 videos viales de referencia se
  completa en un tiempo no mayor a dos veces la duración de su video de origen, en el hardware
  documentado para la medición.
- **SC-004**: El 100% de los trabajos completados del conjunto de prueba publica detecciones con
  clase, confianza, ubicación, número de fotograma y `track_id`, además de un resumen coherente y
  un video anotado temporal recuperable.
- **SC-005**: En una prueba de 20 trabajos válidos enviados con el límite de concurrencia
  configurado, el 100% conserva identificadores, progreso, resultados y artefactos aislados de los
  demás trabajos.
- **SC-006**: El 100% de las cancelaciones solicitadas para trabajos no terminales se refleja como
  `cancelled` antes de publicar un artefacto final y sin dejar archivos temporales accesibles.

## Assumptions

- Las credenciales, el formato de errores seguros y la política de artefactos temporales de la
  iteración 001 siguen vigentes y se reutilizan de forma compatible.
- Los videos de prueba y producción son autorizados para el análisis y no se conservarán como
  historial ni se usarán para reentrenamiento.
- Los límites de concurrencia y tiempo máximo se definirán como configuración externa durante la
  planificación. El perfil inicial de video aceptado está definido en FR-003.
- Los estados, la cola y los datos necesarios para reanudar un trabajo se conservan solo hasta el
  vencimiento temporal configurado; después se eliminan junto con sus artefactos. El resultado y
  metadatos de un trabajo completado están disponibles por 60 minutos.
- El modelo aprobado dispone de clases de actores viales compatibles con el rastreador seleccionado;
  cambios de pesos, umbral o rastreador requerirán métricas comparativas documentadas.
- ByteTrack es el rastreador de referencia de esta iteración. BoT-SORT se evaluará únicamente en
  una iteración o prueba comparativa futura; no forma parte de esta entrega.
- El seguimiento persiste únicamente mientras la asociación visual sea posible; no constituye una
  identificación de personas o vehículos.
- La conservación o reproducción de audio no es un resultado garantizado de esta iteración.
- Cámara en tiempo real, frontend, conteo por línea, OCR o almacenamiento de placas e historial
  permanente están fuera de alcance.
