# Feature Specification: Conteo de actores por línea

**Feature Branch**: 003-conteo-por-linea

**Created**: 2026-11-13

**Status**: Draft

**Input**: Configurar una línea mediante dos puntos sobre un video terminado, contar los cruces de actores rastreados sin duplicarlos, distinguir sentidos, publicar totales por clase y dirección, y mostrar el resultado en un video anotado; sin frontend en esta iteración.

## Clarifications

### Session 2026-11-13

- Q: ¿La solicitud de conteo debe devolver el resultado inmediatamente o crear un trabajo temporal para consultarlo después? → A: Opción B: crear un trabajo temporal de conteo asíncrono, con progreso, eventos de cruce y totales acumulados consultables durante su ejecución.
- Q: ¿Qué punto del actor debe usarse para decidir si cruzó la línea? → A: Opción A: usar el centro de la caja delimitadora del actor.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Configurar un conteo sobre un video terminado (Priority: P1)

Como usuario autorizado, quiero enviar los dos extremos de una línea sobre mi video vial terminado para definir el punto donde deseo contar actores.

**Why this priority**: Sin una línea válida no existe una zona de conteo que el usuario pueda interpretar ni resultados que entregar a una interfaz futura.

**Independent Test**: Sobre un video terminado y vigente, el usuario registra dos puntos distintos dentro del marco y obtiene una configuración asociada únicamente con su propio video.

**Acceptance Scenarios**:

1. **Given** un video terminado, vigente y perteneciente al usuario, **When** envía dos puntos distintos expresados como proporciones del ancho y alto, **Then** recibe una configuración y trabajo temporal con identificadores únicos y puntos normalizados publicados.
2. **Given** un punto fuera del marco, no numérico o una línea de longitud cero, **When** intenta configurar el conteo, **Then** recibe un error claro y no se crea configuración ni resultado.
3. **Given** un video inexistente, vencido, no terminado o perteneciente a otra credencial, **When** intenta configurarlo, **Then** no se revela información del video ni se crea un conteo.

---

### User Story 2 - Consultar conteos por clase y sentido (Priority: P2)

Como usuario autorizado, quiero consultar el avance y los totales acumulados de mi conteo por clase y sentido para comprender el flujo vial mientras se procesa el video.

**Why this priority**: El total confiable por dirección y clase es el valor analítico principal de la funcionalidad.

**Independent Test**: Con detecciones rastreadas controladas que cruzan una línea, el resultado muestra un único evento por actor, la clase correspondiente y la dirección correcta.

**Acceptance Scenarios**:

1. **Given** una configuración válida y actores rastreados que cambian de lado de la línea, **When** se procesa el cálculo, **Then** el usuario puede consultar progreso y totales acumulados separados para A_to_B y B_to_A, agrupados por clase.
2. **Given** un actor que permanece al mismo lado, toca la línea sin cambiar de lado o vuelve a cruzar tras ser contado, **When** se calcula el resultado, **Then** el contador no aumenta más de una vez para ese actor y esa configuración.
3. **Given** varios actores y clases que cruzan en sentidos distintos, **When** el usuario consulta el detalle, **Then** cada evento muestra actor rastreado, clase, sentido, fotograma y momento relativo sin exponer información de otros usuarios.

---

### User Story 3 - Revisar el resultado visual del conteo (Priority: P3)

Como usuario autorizado, quiero recuperar un video anotado con la línea y los contadores para verificar visualmente el resultado del conteo.

**Why this priority**: La evidencia visual permite comprobar que la configuración representa el lugar real del conteo antes de tomar decisiones con los totales.

**Independent Test**: Sobre un video controlado con cruces conocidos, el resultado visual muestra la línea configurada, etiquetas de sentido y totales coherentes con los eventos publicados.

**Acceptance Scenarios**:

1. **Given** un conteo terminado, **When** el usuario recupera el resultado visual vigente, **Then** observa la línea, los nombres de ambos sentidos y los totales por clase sobre el video.
2. **Given** que vence el resultado temporal, **When** el usuario intenta recuperarlo, **Then** el servicio informa el vencimiento sin conservar el video como historial permanente.

### Edge Cases

- Un actor inicia o termina sobre la línea: no se cuenta hasta observar dos lados no nulos y distintos. Una observación exactamente sobre la línea no reemplaza el último lado no nulo; por tanto, la secuencia lado A → línea → lado B constituye un único cruce válido cuando se observa el lado B.
- Dos actores con clases distintas cruzan en el mismo fotograma: ambos generan eventos separados.
- El seguimiento se pierde y reaparece con otro identificador: se trata como un nuevo actor; el sistema no afirma una identidad real.
- El video o sus detecciones expiran durante el cálculo: no se publica un resultado parcial.
- El video tiene cero cruces: se publica un resultado válido con totales en cero.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST permitir a un usuario autorizado crear una configuración y trabajo temporal de conteo para un único video terminado, vigente y de su propiedad.
- **FR-002**: El sistema MUST aceptar una sola línea definida por dos puntos distintos con coordenadas normalizadas entre 0 y 1, inclusive, para que una interfaz futura pueda enviarla después de dibujarla mediante arrastre.
- **FR-003**: El sistema MUST rechazar puntos fuera de rango, no finitos, una línea de longitud cero, videos no terminados, vencidos, inexistentes o no autorizados antes de calcular o publicar resultados.
- **FR-004**: El sistema MUST determinar un cruce válido cuando el centro de la caja delimitadora de un actor rastreado pasa de un lado de la línea al otro entre observaciones consecutivas.
- **FR-005**: El sistema MUST registrar como máximo un evento por combinación de actor rastreado y configuración de línea, aunque el actor vuelva a cruzar posteriormente.
- **FR-006**: El sistema MUST clasificar cada evento como A_to_B o B_to_A según el cambio de lado respecto a la orientación de los dos puntos configurados.
- **FR-007**: El sistema MUST publicar totales por clase y por sentido, además de eventos con actor rastreado, clase, sentido, fotograma y momento relativo.
- **FR-007a**: El sistema MUST publicar durante la ejecución el estado, porcentaje de avance, eventos de cruce confirmados y totales acumulados del trabajo de conteo, sin requerir que termine el video.
- **FR-008**: El sistema MUST generar un resultado visual temporal que muestre línea, etiquetas de dirección, actores rastreados y contadores consistentes con los totales publicados.
- **FR-009**: El sistema MUST mantener aisladas por credencial todas las configuraciones, eventos, totales y resultados visuales, sin exponer rutas internas, secretos ni contenido de otro usuario.
- **FR-010**: El sistema MUST reutilizar exclusivamente detecciones y seguimientos ya disponibles del video terminado; no debe volver a detectar actores para calcular el conteo.
- **FR-011**: El sistema MUST conservar resultados de conteo solo mientras permanezcan vigentes los datos temporales del video de origen y eliminar resultados vencidos o parciales.
- **FR-012**: El sistema MUST registrar el identificador de configuración, video de origen, duración del cálculo, cantidad de eventos y errores seguros, sin secretos, rutas internas ni contenido sensible.
- **FR-013**: El sistema MUST publicar un contrato documentado para crear, consultar y recuperar temporalmente resultados de conteo, compatible con los patrones de autorización y errores existentes.

### Key Entities

- **Configuración de línea**: Dos puntos normalizados, video de origen, propietario y vencimiento.
- **Trabajo de conteo**: Unidad temporal asociada a una configuración que comunica estado, avance, eventos confirmados, totales acumulados y vencimiento.
- **Línea de conteo**: Segmento orientado desde el punto A al punto B; establece los sentidos A_to_B y B_to_A.
- **Evento de cruce**: Registro temporal de un cruce único del centro de la caja de un actor rastreado, con clase, sentido, fotograma y momento relativo.
- **Resumen de conteo**: Totales por clase y sentido asociados con una configuración de línea.
- **Resultado visual de conteo**: Video temporal anotado con línea, direcciones y contadores.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100% de configuraciones con dos puntos válidos sobre videos terminados recibe la confirmación de su trabajo de conteo en un máximo de 2 segundos.
- **SC-002**: El 100% de configuraciones inválidas o no autorizadas se rechaza sin crear eventos ni resultados visuales.
- **SC-003**: En un conjunto controlado de al menos 10 videos con cruces conocidos, el 100% de los actores que cruzan una vez se contabiliza una sola vez en la dirección y clase esperadas.
- **SC-004**: En el mismo conjunto, el 100% de actores que no cambian de lado no genera un evento de conteo.
- **SC-005**: El 100% de resultados visuales disponibles muestra una línea y totales que coinciden con el resumen publicado.
- **SC-006**: El 100% de solicitudes entre dos credenciales distintas conserva el aislamiento de configuraciones, eventos y videos.

## Assumptions

- La futura interfaz convierte las coordenadas obtenidas al arrastrar el mouse a valores normalizados antes de enviarlas; esta iteración no incluye interfaz gráfica.
- La posición del actor para el conteo es el centro de su caja delimitadora; un roce parcial de la caja con la línea no constituye por sí solo un cruce.
- Cada configuración contiene exactamente una línea y usa las etiquetas neutras A_to_B y B_to_A; nombres como entrada/salida podrán configurarse en una iteración posterior.
- El conteo se calcula después de que el video original termina y mientras sus detecciones, seguimientos y artefactos temporales sigan vigentes.
- Las clases provienen del modelo aprobado; no se crean clases nuevas en esta iteración.
- Cámara en tiempo real, múltiples líneas simultáneas, zonas poligonales, OCR, placas, persistencia histórica, alertas y frontend quedan fuera de alcance.

