# Feature Specification: Video progresivo con navegación acotada y enriquecimiento

**Feature Branch**: `feature/009-video-progresivo`

**Created**: 2026-11-22

**Status**: Draft — validada para planificación

**Input**: User description: "Crea la siguiente iteración para ver el video mientras se procesa, bloquear el avance a zonas sin analizar y permitir retroceder, con enriquecimiento progresivo. Crea la rama en el checkout principal y haz commit."

**Reference**: [008-exploracion-imagen-video](../008-exploracion-imagen-video/spec.md) y [007-anotaciones-placas-legibles](../007-anotaciones-placas-legibles/spec.md).

**Contexto**: El flujo actual espera al análisis completo para reproducir. El usuario aportó un trabajo que agotó 300 segundos de procesamiento tras 2.461 de 3.611 cuadros. La duración máxima del archivo y el plazo para procesarlo son límites distintos; esta evidencia motiva resultados anticipados, sin constituir una medición general ni una garantía de tiempo real.

**Alcance de esta etapa**: Especificación y checklist en el checkout principal con rama nueva y commit. La implementación posterior comprende backend y frontend, conservando su separación, los cambios existentes y Speckit en la raíz.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver el tramo analizado mientras continúa el trabajo (Priority: P1)

Como usuario, quiero reproducir una primera parte del video con sus cajas sin esperar a que termine todo el análisis ni el enriquecimiento.

**Why this priority**: Reduce la espera sin presentar escenas pendientes como si ya estuvieran analizadas.

**Independent Test**: Usar un video controlado cuyo análisis avance por tramos y observar inicio, continuidad, espera y reanudación.

**Acceptance Scenarios**:

1. **Given** un análisis activo, **When** está disponible su tramo inicial, **Then** se habilita reproducirlo con sus cajas, duración y velocidad originales sin esperar el análisis completo ni todas las lecturas de placas.
2. **Given** reproducción activa, **When** se confirman nuevos tramos continuos, **Then** se incorporan sin reiniciar el reproductor, duplicar cuadros o cambiar la posición elegida.
3. **Given** reproducción que alcanza el límite disponible, **When** el siguiente tramo no está analizado o no puede recuperarse, **Then** se pausa dentro del intervalo permitido y explica que espera más contenido analizado.
4. **Given** pausa automática por espera, **When** existe de nuevo un margen suficiente, **Then** se reanuda desde el mismo punto a velocidad normal; una pausa manual del usuario no se reanuda sola.
5. **Given** un tramo sin vehículos o un archivo más corto que el margen inicial, **When** ese tramo o archivo termina de analizarse, **Then** puede reproducirse sin cajas y sin esperar detecciones inexistentes o un margen imposible.

---

### User Story 2 - Retroceder y volver hasta el límite analizado (Priority: P1)

Como usuario, quiero distinguir mi posición del avance del análisis y moverme por las partes disponibles sin entrar en zonas pendientes.

**Why this priority**: La inspección repetida debe aprovechar resultados existentes y respetar la disponibilidad del análisis.

**Independent Test**: Con un video de 120 segundos y disponibilidad hasta 42 segundos, probar saltos a 10, 30, 42, 60 y 120 mediante todos los controles expuestos.

**Acceptance Scenarios**:

1. **Given** reproducción en 18 y disponibilidad hasta 42 de 120 segundos, **When** se observa la barra, **Then** se distinguen posición, tramo analizado y zona pendiente, con tiempos comprensibles.
2. **Given** disponibilidad hasta 42, **When** se solicita ir a 10 o 30, **Then** se permite el salto y se muestran las cajas de ese instante sin repetir análisis.
3. **Given** disponibilidad hasta 42, **When** se intenta ir a 60 o al final, **Then** se bloquea el salto, la posición permanece dentro del tramo disponible y se indica el motivo.
4. **Given** revisión del segundo 10, **When** el límite aumenta de 42 a 55, **Then** la posición permanece en 10 y se habilita avanzar hasta el nuevo límite.
5. **Given** teclado, toque, arrastre o controles alternativos del reproductor, **When** se intenta superar el límite, **Then** se aplica la misma restricción, incluso en pantalla completa.
6. **Given** un salto válido cuyas anotaciones requieren recuperarse, **When** aún no están listas, **Then** se espera su recuperación sin mostrar las cajas del instante anterior ni repetir inferencia.

---

### User Story 3 - Inspeccionar vehículos con enriquecimiento progresivo (Priority: P1)

Como usuario, quiero pausar, seleccionar un vehículo y consultar datos y evidencia mientras el resto del video sigue analizándose.

**Why this priority**: Los resultados tempranos deben ser útiles sin que una lectura lenta bloquee el video.

**Independent Test**: Consultar varios Track ID en un tramo con atributos y placas pendientes, disponibles, no aplicables y fallidos; actualizar resultados sin mover la reproducción.

**Acceptance Scenarios**:

1. **Given** un vehículo elegible con evidencia confirmada, **When** el video todavía se está analizando, **Then** se permite solicitar su enriquecimiento al seleccionarlo, y la ficha indica el estado real sin consultar los otros vehículos.
2. **Given** un video pausado, **When** se selecciona una caja o su alternativa en la lista, **Then** se identifica el mismo Track ID real y se muestran clase, atributos, estado de placa y evidencia autorizada disponible.
3. **Given** una ficha pendiente, **When** llega un resultado de ese vehículo, **Then** se actualiza sin mover el video, cambiar la selección o asociarlo a otra identidad.
4. **Given** atributos parciales, ausencia de placa o lectura fallida, **When** se consulta la ficha, **Then** se distinguen de una espera activa y se conservan los datos válidos y la reproducción.
5. **Given** el mismo Track ID en varios tramos, **When** se recibe más evidencia o se vuelve a una aparición anterior, **Then** conserva su identidad dentro del trabajo y se indica el instante de la evidencia; navegar no genera análisis duplicados.
6. **Given** reproducción activa, **When** se selecciona un vehículo desde un control disponible, **Then** se pausa para inspeccionarlo; cerrar la ficha no reanuda una pausa manual automáticamente.

---

### User Story 4 - Recuperar lo disponible y entender fallos y esperas (Priority: P2)

Como usuario, quiero aprovechar los tramos confirmados ante un fallo posterior y distinguir espera, error, cancelación y vencimiento.

**Why this priority**: Un corte no debe ocultar automáticamente el trabajo útil ya publicado, ni conservar evidencia cuando corresponde retirarla.

**Independent Test**: Interrumpir conexión, agotar el tiempo de análisis y fallar enriquecimiento después de publicar un tramo; repetir con cancelación, cambio de archivo y vencimiento.

**Acceptance Scenarios**:

1. **Given** tramos disponibles y desconexión temporal, **When** se recupera el acceso al mismo trabajo vigente, **Then** se consultan su límite y resultados sin crear otro análisis; la desconexión no habilita intervalos desconocidos.
2. **Given** un fallo o agotamiento de tiempo después de publicar un tramo, **When** se informa el error, **Then** la parte confirmada sigue consultable mientras su autorización y vigencia lo permitan, el límite deja de avanzar y el resultado se identifica como parcial.
3. **Given** fallo de análisis con enriquecimiento asociado, **When** existen datos válidos publicados, **Then** se conservan y se informa si las lecturas restantes concluyeron, fallaron o se cancelaron, sin esperas indefinidas.
4. **Given** cancelación explícita, limpieza, sustitución de archivo o rechazo de acceso, **When** llega una respuesta antigua, **Then** no restaura medios, cajas ni fichas retiradas.
5. **Given** vencimiento de la fuente o un resultado, **When** se alcanza su plazo, **Then** se retiran los datos afectados, incluso si estaban pausados o en un modo oculto.
6. **Given** videos con distintas velocidades de análisis, **When** se muestra progreso, **Then** se distinguen duración del archivo, tiempo de procesamiento y tramo reproducible; una estimación no se presenta como finalización garantizada.

### Edge Cases

- Tramo inicial o final menor que el margen requerido; cuadros sin vehículos; video sin vehículos elegibles.
- Intervalos de distinta duración entre cuadros, oclusiones, pérdida de seguimiento, movimiento rápido o cambios de escena.
- Información duplicada, antigua, fuera de orden o incompleta; un hueco entre tramos no se habilita por tomar el mayor tiempo recibido.
- Cuadros analizados cuyos medios o anotaciones aún no pueden recuperarse para reproducir.
- Arrastre repetido contra el límite, avance rápido, tecla de fin y cambios entre pausa manual, reproducción y espera.
- Salto, cambio de tamaño, pantalla completa, cambio de modo o texto ampliado mientras llegan nuevos resultados.
- Fallo antes del primer tramo o interrupción del proceso después de publicar resultados.
- Evidencia de otro instante, lectura refinada, Track ID repetido en otro trabajo o respuesta antigua tras sustituir la fuente.
- Dos propietarios intentando consultar la misma fuente; acceso rechazado o evidencia que vence durante la inspección.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST permitir reproducir el tramo inicial de un video aceptado antes de finalizar su análisis, cuando sus medios y resultados estén confirmados y disponibles.
- **FR-002**: El límite disponible MUST ser el final del intervalo continuo desde el inicio que pueda reproducirse con resultados confirmados y autorizados. Un cuadro sin vehículos cuenta como analizado; un hueco o una estimación de progreso no cuenta como disponible.
- **FR-003**: El límite MUST avanzar solo después de confirmar los resultados del tramo correspondiente. Datos repetidos, antiguos o fuera de orden no deben hacerlo retroceder ni habilitar huecos; vencimiento o rechazo de acceso retiran la disponibilidad afectada.
- **FR-004**: El reproductor MUST impedir situarse o continuar más allá del límite disponible mediante cualquiera de los controles que exponga. La detención observada admite como máximo la tolerancia de un intervalo de cuadro.
- **FR-005**: El usuario MUST poder retroceder y volver a avanzar dentro de los tramos disponibles sin repetir inferencia. La llegada de nuevos resultados no debe desplazarlo.
- **FR-006**: La barra MUST distinguir posición de reproducción, tramo disponible y zona pendiente, con tiempos comprensibles e indicaciones que no dependan solo del color; la duración debe identificarse como conocida o estimada.
- **FR-007**: Al agotar el contenido disponible, el reproductor MUST pausarse dentro del límite e informar espera de análisis o recuperación. Debe reanudar solo una pausa automática cuando haya margen suficiente; la pausa manual tiene prioridad.
- **FR-008**: Inicio y reanudación MUST requerir un margen disponible ajustable por operación. Un archivo terminado o un resultado parcial válido debe permitir reproducir su resto disponible aunque sea menor que ese margen.
- **FR-009**: La reproducción MUST conservar velocidad normal de 1x, orden, proporciones, duración y correspondencia temporal de la fuente. No debe saltar cuadros ni variar la velocidad para ocultar retrasos.
- **FR-010**: Las cajas MUST corresponder al instante y Track ID reproducidos, conservar colores sólidos por clase y legibilidad, sin numeraciones que tapen vehículos. Un salto temporal debe retirar las cajas anteriores hasta disponer de las correctas.
- **FR-011**: Reproducción y navegación MUST funcionar durante el enriquecimiento y sin esperar una exportación completa del video anotado. El resultado final y el conteo existentes deben conservar su disponibilidad y significado.
- **FR-012**: El nuevo frontend MUST iniciar enriquecimiento únicamente al seleccionar explícitamente un vehículo elegible, durante una pausa o pausando la reproducción al seleccionarlo. No se consultan automáticamente los demás vehículos. La solicitud identifica trabajo/Track ID/evidencia y mantiene su estado independiente.
- **FR-013**: El enriquecimiento solicitado MUST reutilizar resultados vigentes del vehículo. La primera solicitud congela hasta K evidencias confirmadas disponibles; repetir selección no vuelve a evaluar ni refina automáticamente con evidencias futuras. Se conserva el modo automático de los clientes previos que no opten por la política bajo demanda.
- **FR-014**: El usuario MUST poder pausar y seleccionar un vehículo mediante su caja o alternativa accesible para consultar clase, Track ID, atributos, placa y evidencia disponible. Seleccionar durante la reproducción debe pausarla para inspección.
- **FR-015**: Las fichas MUST distinguir pendiente, disponible, parcial, no aplicable, fallido y vencido. Actualizarlas no debe mover el video, cambiar la selección, inventar datos o presentar evidencia representativa como si perteneciera al cuadro actual.
- **FR-016**: La interfaz MUST separar avance del análisis, disponibilidad reproducible y estado de consulta del vehículo seleccionado. No muestra barra global de enriquecimiento en el modo bajo demanda. Duración máxima del archivo, tiempo permitido de procesamiento y tramo reproducible son conceptos distintos; el conteo opcional ocupa la sección inferior.
- **FR-017**: Tras una desconexión recuperable, el usuario MUST poder consultar el mismo trabajo vigente y sus resultados confirmados sin crear un nuevo análisis. No se debe prometer reanudación de inferencia cuando solo se recupera una consulta.
- **FR-018**: Fallo técnico o agotamiento del tiempo MUST detener el avance y conservar los tramos publicados todavía autorizados y vigentes como resultado parcial. Las lecturas restantes deben terminar o alcanzar un estado terminal explícito; no deben quedar pendientes indefinidamente. Un fallo de exportación final no retira por sí solo esos tramos.
- **FR-019**: Cancelación explícita, limpieza, cambio de archivo, rechazo de acceso y vencimiento MUST retirar la evidencia afectada y bloquear su restauración por respuestas tardías. Conservar un resultado parcial no amplía su retención ni concede acceso a otro propietario.
- **FR-020**: Medios parciales, anotaciones y enriquecimiento MUST mantener los controles de acceso y privacidad existentes. No se deben publicar credenciales ni convertir medios o lecturas sensibles en contenido público o datos de diagnóstico.
- **FR-021**: Controles y estados MUST mantener coherencia con Imagen, colores sin gradientes, teclado y toque, foco visible y etiquetas comprensibles, en móvil, tablet, escritorio y texto al 200 % sin desplazamiento horizontal de página.
- **FR-022**: La entrega MUST comparar contra el flujo actual, con los mismos videos y equipo, espera hasta primera reproducción, avance del análisis, fluidez, pausas, tiempo total y memoria. Cambiar muestreo, modelo o calidad requiere evaluación y decisión documentada; esta especificación no autoriza degradarlos.
- **FR-023**: La implementación MUST preservar análisis de imágenes, límites de admisión y funciones existentes. Debe planificar explícitamente cambios del backend y frontend, sin modificar automáticamente límites, credenciales, pesos o políticas de retención para aparentar mejora.

### Key Entities *(include if feature involves data)*

- **Trabajo de video**: Fuente aceptada, propietario, duración, estado, tiempos, motivo de fallo y vigencia.
- **Tramo confirmado**: Intervalo con medios y observaciones disponibles, incluidos cuadros sin detecciones; integra el resultado parcial o final.
- **Límite disponible**: Último instante continuo desde el inicio reproducible con resultados confirmados y autorizados; diferente de progreso estimado y posición actual.
- **Estado de reproducción**: Posición, intención del usuario, pausa manual o automática, margen disponible y estado de recuperación.
- **Observación de vehículo**: Identidad dentro del trabajo, instante, clase, geometría y validez de seguimiento.
- **Evidencia y enriquecimiento**: Datos de un Track ID, instante representativo, atributos, placa, procedencia, estado y vencimiento, sin superar la vida útil de su fuente autorizada.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En el 100 % de videos controlados de al menos 30 segundos cuyo análisis continúe activo tras confirmar cinco segundos iniciales, el usuario puede empezar a ver esa parte en un máximo de dos segundos desde su disponibilidad, sin esperar el resto del análisis ni el enriquecimiento.
- **SC-002**: El 100 % de intentos de salto a zonas pendientes mediante controles expuestos queda bloqueado. Al alcanzar el límite reproduciendo, no se presenta contenido posterior salvo una tolerancia de un intervalo de cuadro; al concluir se habilita toda la duración confirmada.
- **SC-003**: En al menos el 95 % de 30 saltos dentro de tramos disponibles, se recuperan imagen y cajas correctas en menos de un segundo, en condiciones de referencia documentadas y sin inferencia adicional. Se incluyen retrocesos y regreso al límite.
- **SC-004**: En clips controlados con al menos diez vehículos identificados y varios tramos, el 100 % de fichas mantiene asociación con trabajo y Track ID correctos; los datos confirmados aparecen en un máximo de dos segundos desde su disponibilidad, sin desplazar la reproducción.
- **SC-005**: El desfase entre cuadros y anotaciones no supera un intervalo de cuadro en reproducción, pausa, salto, cambio de tamaño y pantalla completa. Las pérdidas de seguimiento y cambios de escena no dejan cajas persistentes sin observaciones válidas.
- **SC-006**: Con contenido suficiente disponible, al menos el 95 % de las ventanas de cinco segundos de reproducción alcanza el 90 % de los cuadros por segundo de la fuente, con velocidad 1x. Las pausas por espera, saltos y pausas manuales se contabilizan por separado y se informa la proporción del tiempo total en espera.
- **SC-007**: El tiempo total de análisis no supera el 110 % de la línea base en el mismo equipo, videos y calidad de análisis, manteniendo el enriquecimiento habilitado en ambos recorridos. La evaluación define antes de medir fases, concurrencia y repeticiones, compara memoria y tiempo por fase y conjunto, y no oculta esperas o pérdidas de cobertura.
- **SC-008**: En el 100 % de casos controlados de desconexión, fallo posterior a un tramo, cancelación, vencimiento y respuesta tardía, se conserva o retira lo definido sin mezclar trabajos ni conceder acceso indebido.
- **SC-009**: En pruebas de uso con cinco participantes y las tres familias de pantalla, al menos cuatro distinguen sin ayuda posición y límite analizado, retroceden, regresan al último tramo e inspeccionan un vehículo. Los flujos esenciales se completan también con teclado y texto al 200 %.

- **SC-010**: En las mismas condiciones de SC-007, la memoria máxima conjunta del análisis y enriquecimiento no supera el 120 % de la línea base. Se informa también la memoria del reproductor; los resultados recibidos no deben causar crecimiento indefinido al retroceder repetidamente por el mismo video.

## Assumptions

- Se incluyen videos subidos por archivo. Cámaras, emisiones en directo y análisis antes de completar la subida quedan fuera de alcance.
- Se considera una reproducción activa por usuario y trabajo; cambiar entre Imagen y Video conserva el estado vigente conforme a 008.
- El margen inicial de referencia es de cinco segundos analizados y puede ajustarse operativamente. No garantiza una espera total de cinco segundos; los archivos o restos más cortos siguen FR-008.
- El análisis puede avanzar más lento que la reproducción. Se aceptan pausas de espera explícitas; no se promete continuidad desde el inicio en cualquier hardware ni se cambia la velocidad para aparentar tiempo real.
- La planificación debe fijar las condiciones reproducibles de evaluación antes de medir. Los umbrales de aceptación no se reemplazan posteriormente por los resultados obtenidos.
- Se conservan modelo aprobado, seguimiento, colores por clase y criterios de calidad. Una optimización que los afecte requiere evaluación independiente conforme a la constitución; cambiar a aceleración de hardware no es requisito previo del flujo progresivo.
- Son dependencias necesarias la disponibilidad de resultados parciales autorizados, la reproducción de tramos vigentes y el enriquecimiento previo al cierre completo. Deben planificarse cambios explícitos en backend y frontend conservando la protección de acceso.
- La fuente necesaria para reproducir y la evidencia mínima permanecen únicamente durante su vigencia autorizada; publicar tramos no reinicia el plazo ni crea un historial permanente.
- Ante un fallo se recupera lo confirmado, sin prometer reanudar automáticamente inferencia desde el cuadro interrumpido tras reiniciar el servicio. Recuperar una consulta vigente no equivale a reiniciar procesamiento.
- La selección de vehículos pausados en video incorpora ahora la interacción propuesta en 008. No se incluyen búsqueda por placa, exportación de informes, análisis de audio ni nuevas políticas de reconocimiento.
- Se conserva backend/ y frontend/, con .specify/, .agents/, specs/ y metricas/ en la raíz. La iteración no cambia el estado de aceptación ni cierra pendientes de 006, 007 u 008.


## Cambio de alcance aprobado — 2026-11-22

El usuario aprobó implementar detección/seguimiento primero, enriquecimiento solo al seleccionar y conteo opcional. Esta decisión sustituye el automatismo de la historia3 para el nuevo frontend, conservando clientes anteriores. No se altera modelo, muestreo ni calidad de detección; la prueba larga sigue diferida.

- **FR-024**: El panel lateral de Video MUST conservar la jerarquía visual de Imagen: ficha, clase/Track ID, recorte de vehículo, atributos, placa y recorte de placa. La lista no precede a la ficha: existe una alternativa compacta para vehículos del fotograma actual debajo del reproductor.
- **FR-025**: El usuario MUST poder activar/desactivar conteo por línea en una sección inferior, eligiendo dos puntos en un fotograma confirmado mediante toque/puntero o controles de teclado, sin iniciar otra detección.
- **FR-026**: La línea configurada MUST aparecer sobre el video principal y el contador en su esquina superior derecha. El acumulado corresponde al instante reproducido, no al prefijo futuro ya analizado. Retroceder/repetir un tramo no duplica eventos. La dirección y regla de un cruce por Track ID conservan el conteo existente; cambios de línea recalculan a partir de trayectorias persistidas.
- **AC adicional**: Antes de seleccionar, un clip con vehículos no ejecuta atributos/localización/OCR. Seleccionar uno habilita sus recortes y datos; repetir selección utiliza caché. Dibujar una línea, ir antes/después de un cruce y retroceder muestra0/1/0 sin otra subida ni inferencia.
