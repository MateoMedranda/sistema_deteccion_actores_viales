# Feature Specification: Inspección de video consistente, cruces dirigidos y resumen por clase

**Feature Branch**: `feature/010-video-detalle-conteo`

**Created**: 2026-11-24

**Status**: Draft — validada para planificación

**Input**: User description: "En video, la ficha debe verse igual que en imágenes y no tener ese scroll interno. El video exportado debe llevar etiquetas encima de cada bounding box. Contar solo los vehículos que atraviesan la línea y mejorar el indicador. Evitar que la imagen de enriquecimiento parpadee/cambie o muestre al vehículo cuando apenas entraba. Al final mostrar cuántos vehículos de cada clase se detectaron en todo el video, independientemente del conteo. Crear otra iteración con speckit-specify, rama y commits."

**Aclaración del usuario**: El conteo será en un solo sentido elegido, indicado con una flecha.

**Referencias**: [009-video-progresivo](../009-video-progresivo/spec.md), sus enmiendas de consulta bajo demanda y exportación explícita, y [006-mejoras-frontend](../006-mejoras-frontend/spec.md)/[007-anotaciones-placas-legibles](../007-anotaciones-placas-legibles/spec.md) como base de la ficha de imágenes y colores de clase. Las dos capturas aportadas sirven de referencia visual, sin incorporar sus medios privados al repositorio.

**Contexto**: La ficha de video presenta una barra vertical propia; la consulta puede mostrar evidencia de un instante anterior a la selección. El conteo actual expone dos sentidos y debe distinguirse del inventario total de vehículos descubiertos. Estos son problemas observados de experiencia y resultados; sus causas concretas se verificarán durante la planificación, sin atribuirlas todavía al modelo.

**Alcance de esta etapa**: Especificación, checklist, registro metodológico y commit en el checkout principal. La posterior implementación abarca las capacidades de frontend/backend necesarias. Se mantienen su separación y Speckit en la raíz. Esta etapa no modifica código ejecutable ni implementa las mejoras.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consultar una ficha igual de clara que en imágenes (Priority: P1)

Como usuario, quiero inspeccionar un vehículo del video con la misma distribución, tipografía, jerarquía y controles de la ficha de imágenes, sin una segunda barra de desplazamiento para toda la ficha.

**Why this priority**: La inconsistencia y el desplazamiento anidado dificultan ver recortes, atributos y placa.

**Independent Test**: Comparar fichas equivalentes de imagen y video con todos sus apartados, en escritorio, tablet y móvil, recorriendo la página con ratón, toque y teclado.

**Acceptance Scenarios**:

1. **Given** un video pausado y un vehículo seleccionado, **When** se abre su ficha, **Then** usa el mismo lenguaje visual y orden de contenidos que imágenes: identificación, recorte, atributos y placa con sus controles disponibles; conserva Track ID y referencia temporal propios del video.
2. **Given** una ficha más alta que el área visible, **When** se consulta su contenido, **Then** la página permite llegar al final y cerrar la ficha sin una barra vertical independiente que recorte toda la ficha.
3. **Given** una pantalla móvil o tablet, **When** cambia la distribución, **Then** video y ficha se reorganizan sin ocultar datos ni provocar desplazamiento horizontal de la página; la selección y los controles siguen accesibles.

---

### User Story 2 - Inspeccionar evidencia del instante seleccionado sin parpadeos (Priority: P1)

Como usuario, quiero que al pausar y seleccionar un vehículo su recorte y enriquecimiento correspondan a ese instante, y permanezcan estables durante la consulta.

**Why this priority**: Un recorte antiguo o cambiante impide comprobar qué vehículo y placa fueron consultados, aunque el Track ID sea el mismo.

**Independent Test**: Seleccionar el mismo vehículo primero al entrar y después cuando se ve de cerca; introducir respuestas retrasadas, actualizaciones del análisis y cambios rápidos de selección.

**Acceptance Scenarios**:

1. **Given** un vehículo apenas visible a los 3 segundos y claramente visible a los 20, **When** se selecciona a los 20, **Then** se muestra el recorte de la selección y se consulta ese contexto temporal; no se reutiliza silenciosamente el recorte ni una lectura negativa de la consulta de los 3 segundos.
2. **Given** una consulta abierta, **When** llegan actualizaciones del análisis o de la consulta, **Then** se mantienen el vehículo, instante y recortes elegidos; los datos pendientes pueden completarse sin alternar imágenes, vaciarlas periódicamente o reiniciar sus controles de inspección.
3. **Given** selección de un segundo vehículo o de otro instante antes de terminar la consulta anterior, **When** llega una respuesta retrasada, **Then** no reemplaza la ficha nueva ni mezcla vehículo, atributos, placa o recortes de ambas consultas.
4. **Given** una consulta ya resuelta para el mismo vehículo e instante, **When** se vuelve a abrir sin cambiar la evidencia, **Then** se reutiliza el resultado disponible sin trabajo duplicado. Seleccionar el mismo vehículo en un instante diferente permite una consulta nueva sobre su evidencia correspondiente.
5. **Given** ausencia de evidencia válida en el instante solicitado, **When** se abre la ficha, **Then** se explica la limitación y cualquier alternativa temporal se presenta con su instante real para elección expresa; no se sustituye automáticamente por una imagen antigua o de otro vehículo.

---

### User Story 3 - Contar cruces reales en un solo sentido (Priority: P1)

Como usuario, quiero dibujar la línea sobre el primer fotograma, elegir mediante una flecha qué sentido cuenta y sumar únicamente vehículos que atraviesen ese segmento en ese sentido.

**Why this priority**: El indicador debe representar cruces verificables de la línea elegida y permitir interpretar correctamente el sentido del tráfico.

**Independent Test**: Usar trayectorias controladas que crucen en ambos sentidos, pasen cerca, toquen la línea, crucen su prolongación y reaparezcan; revisar el contador al reproducir, retroceder y volver a avanzar.

**Acceptance Scenarios**:

1. **Given** un video seleccionado y todavía sin analizar, **When** se configura el conteo, **Then** se dispone del primer fotograma, colocación y arrastre suave de extremos/segmento, selección del sentido mediante flecha e inversión de esa flecha antes de activar.
2. **Given** conteo activo, **When** el centro del recuadro de un vehículo pasa de un lado al otro atravesando el segmento visible en el sentido elegido y se confirma mediante observaciones reales, **Then** el total aumenta una vez para esa identidad.
3. **Given** vehículos que cruzan al revés, se mantienen al mismo lado, rozan la línea, cruzan su prolongación fuera del segmento o solo presentan una predicción intermedia de cruce, **When** se actualiza el análisis, **Then** no aumentan el total por esos movimientos.
4. **Given** varios cruces válidos en el mismo intervalo, **When** se muestran sus resultados, **Then** se suman todos exactamente una vez; el indicador no usa el número del Track ID como cantidad ni duplica eventos por nuevas consultas.
5. **Given** cruces ya analizados, **When** se retrocede y reproduce otra vez, **Then** el contador muestra el acumulado hasta la posición reproducida y vuelve al mismo valor al regresar; la revisión no crea cruces adicionales.
6. **Given** una línea/sentido activos, **When** el usuario solicita cambiarlos, **Then** se muestra el cambio pendiente y su efecto de recalcular; únicamente al aplicar se abre una configuración nueva, sin mezclar sus resultados con la anterior.

---

### User Story 4 - Conocer el total detectado por clase (Priority: P1)

Como usuario, quiero ver al terminar cuántos vehículos de cada clase se detectaron en todo el video, aunque nunca cruzaran una línea o el conteo estuviera desactivado.

**Why this priority**: El inventario de detecciones y los cruces responden preguntas distintas y no deben confundirse.

**Independent Test**: Analizar una escena controlada con identidades repetidas durante muchos cuadros y vehículos que no cruzan; finalizar con conteo activado y desactivado y comprobar el mismo resumen de detecciones.

**Acceptance Scenarios**:

1. **Given** un video completamente analizado, **When** se muestra el resumen, **Then** aparecen el total de vehículos detectados y su distribución por clase, identificados como resultados de todo el video e independientes de los cruces de línea.
2. **Given** un Track ID visible en cientos de cuadros, **When** se calcula el resumen, **Then** aporta una sola unidad y una sola clase consolidada, no una unidad por cuadro ni por consulta de enriquecimiento.
3. **Given** una clase que varía durante observaciones del mismo vehículo, **When** se consolida su resultado, **Then** se aplica una regla consistente documentada y el vehículo no aparece contado simultáneamente en varias clases; la suma por clases coincide con el total.
4. **Given** un video sin detecciones, **When** termina, **Then** el resumen indica cero con un estado comprensible. Si el análisis falla o se cancela, cualquier resumen conservado se marca parcial y precisa el tramo analizado.
5. **Given** un video completo, **When** se retrocede, se cambia la línea o se desactiva el conteo, **Then** el resumen final de detecciones de todo el video no cambia.

---

### User Story 5 - Descargar video con etiquetas legibles (Priority: P2)

Como usuario, quiero que el video anotado que solicito exportar incluya una etiqueta encima de cada caja, con clase e identificador del vehículo y el color de clase correspondiente.

**Why this priority**: La descarga debe permitir entender las detecciones fuera de la aplicación y seguir sus identidades entre cuadros.

**Independent Test**: Exportar una escena controlada con varias clases, vehículos pequeños, cajas próximas al borde y superposiciones; revisar la descarga de principio a fin.

**Acceptance Scenarios**:

1. **Given** un análisis terminado y una exportación solicitada, **When** se descarga y reproduce, **Then** cada caja dibujada lleva una etiqueta con nombre de clase e identificador local estable, situada encima siempre que haya espacio.
2. **Given** una caja junto al borde superior o varias etiquetas próximas, **When** se dibujan, **Then** las etiquetas permanecen dentro del video, conservan contraste y asociación inequívoca con su caja, y se ajustan para reducir el solapamiento sin omitir identidades silenciosamente.
3. **Given** reproducción a velocidad original, **When** avanzan los cuadros, **Then** cajas y etiquetas corresponden al mismo instante e identidad, con los colores de clase usados en la aplicación.
4. **Given** un usuario que solo analiza o reproduce, **When** no solicita exportar, **Then** no se genera video anotado ni se retrasa el análisis por preparar etiquetas de una descarga inexistente.

### Edge Cases

- Fotograma seleccionado correspondiente a una caja predicha entre dos observaciones: no atribuir certeza de una medición a la predicción ni sustituir silenciosamente el instante consultado.
- Vehículo sin placa visible en el instante elegido: mostrar ausencia/no localización de ese contexto; no fabricar caracteres ni reutilizar como definitiva una ausencia de otro instante.
- Respuesta tardía tras cerrar ficha, cambiar de vehículo, buscar otro instante o iniciar otro video: no reabrir ni contaminar la selección actual.
- Recorte retirado o vencido durante la consulta: indicar indisponibilidad sin bucle de recargas ni mostrar datos privados conservados en otro contexto.
- Centro del recuadro exactamente sobre la línea o en un extremo: tocar no basta; se requiere pasar entre lados opuestos y atravesar el segmento, incluidos sus extremos.
- Vehículo presente desde el primer cuadro, sin observación previa al otro lado: no asumir un cruce anterior.
- Cruce entre dos cuadros medidos con una predicción intermedia: confirmar con las mediciones y ubicar el evento de forma consistente en la cronología; la predicción sola no suma.
- Cruces fuera de los extremos de la línea aunque cambie el signo respecto a su prolongación: excluirlos.
- Oscilación de cajas o un mismo vehículo que vuelve a cruzar: el total de una configuración cuenta cada identidad elegible una sola vez, sin duplicar por vibraciones o repetición de la reproducción.
- Cambiar zoom, tamaño de pantalla o pantalla completa: la línea, flecha y cruces conservan su correspondencia con la escena.
- Cambiar el sentido con el análisis parcialmente disponible: recalcular sobre el tramo confirmado y distinguir sus resultados de los de la configuración anterior.
- Trabajo sin vehículos, con clases desconocidas o con cambios de clase: resumen coherente, categoría desconocida explícita cuando proceda y suma sin duplicados.
- Pérdida de seguimiento y nueva identidad para el mismo vehículo físico: el resumen declara su alcance por identidades de seguimiento, sin garantizar una deduplicación física que el sistema no puede acreditar.
- Video antiguo con datos insuficientes para el resumen, enriquecimiento temporal o etiquetas: indicar capacidades disponibles y necesidad de nuevo análisis cuando corresponda; no presentar datos fabricados como resultado completo.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: La ficha de video DEBE mantener la estructura, tipografía, tamaños, espaciado y jerarquía de la ficha de imágenes, añadiendo únicamente el contexto de identidad y tiempo del video.
- **FR-002**: La ficha DEBE mostrar todo su contenido mediante el desplazamiento normal de la página, sin altura limitada que imponga una barra vertical independiente sobre la ficha completa. Se conservan los controles propios de ampliación de recortes y placa.
- **FR-003**: La distribución DEBE adaptarse a escritorio, tablet y móvil sin ocultar acciones o datos ni introducir desplazamiento horizontal de página; selección, cierre, navegación y sentido de conteo DEBEN ser operables con teclado y toque, con foco y etiquetas comprensibles.
- **FR-004**: Cada selección de video DEBE vincular vehículo, instante reproducido y evidencia usada en una consulta identificable. Su enriquecimiento DEBE usar evidencia correspondiente al contexto elegido y mostrar el instante real.
- **FR-005**: El recorte principal DEBE corresponder al vehículo del fotograma seleccionado. Cuando no sea posible obtener evidencia válida de ese contexto, el sistema DEBE explicarlo y solicitar elección expresa de cualquier evidencia alternativa con referencia temporal; no DEBE regresar automáticamente a la primera aparición.
- **FR-006**: Una consulta resuelta o en curso DEBE mantener estables sus recortes y controles frente a consultas periódicas o actualizaciones del trabajo. Completar atributos/placa no DEBE producir sustituciones periódicas, parpadeos ni mezcla de identidades/instantes.
- **FR-007**: Seleccionar otra identidad o un instante distinto DEBE abrir el contexto correcto y protegerlo frente a respuestas anteriores. Repetir el mismo contexto DEBE reutilizar resultados válidos sin duplicar consultas; un resultado antiguo no DEBE impedir consultar evidencia nueva.
- **FR-008**: El enriquecimiento DEBE continuar bajo demanda de los vehículos seleccionados y mostrar espera, éxito, ausencia, fallo o vencimiento sin bloquear el análisis restante ni inventar datos.
- **FR-009**: El editor de línea DEBE conservar el primer fotograma y permitir colocar y arrastrar suavemente extremos y segmento antes de analizar; DEBE permitir escoger e invertir un único sentido, representado claramente mediante una flecha que atraviesa la línea.
- **FR-010**: Un cruce válido DEBE requerir observaciones reales sucesivas de la misma identidad cuyo centro de caja pasa de un lado al otro, intersectando el segmento finito dibujado y siguiendo el sentido elegido. Una posición sobre la línea conserva la última referencia válida de lado hasta poder confirmar o descartar el paso.
- **FR-011**: El conteo DEBE excluir sentido inverso, permanencia en un lado, contacto sin paso, cruces de la prolongación fuera del segmento y predicciones no confirmadas. Los extremos pertenecen al segmento, pero tocarlos sin cambiar de lado no constituye un cruce.
- **FR-012**: Cada identidad DEBE aportar como máximo un cruce en cada configuración activa de línea y sentido; el resultado DEBE ser independiente de actualizaciones repetidas, reintentos y reproducción repetida.
- **FR-013**: El indicador principal DEBE mostrar un único acumulado de cruces del sentido elegido, con flecha/leyenda inequívoca en la esquina superior derecha del video y lectura accesible. Los números de Track ID no DEBEN usarse como cantidades; varios cruces simultáneos aumentan el total en su cantidad real.
- **FR-014**: El indicador DEBE corresponder al instante reproducido y al tramo analizado confirmado. Avanzar suma los cruces nuevos; retroceder recupera el acumulado histórico sin registrar nuevos eventos ni mostrar cruces futuros como si ya hubieran ocurrido.
- **FR-015**: Cambiar línea o sentido DEBE aplicarse como una nueva configuración con recálculo sobre observaciones conservadas, sin mezclar acumulados anteriores ni repetir detección del video. Desactivar el conteo DEBE conservar la disponibilidad de análisis y resumen por clase.
- **FR-016**: Al completar el análisis, el sistema DEBE ofrecer un resumen final con total de identidades de vehículos detectadas y cantidad por clase para todo el video, independiente del estado/configuración del conteo o del enriquecimiento.
- **FR-017**: El resumen DEBE contar una sola vez cada identidad confirmada del trabajo y asignarle una clase consolidada mediante una regla determinista documentada durante la planificación; la suma por clases DEBE coincidir con el total. Clase desconocida no DEBE perderse silenciosamente.
- **FR-018**: Resúmenes de análisis incompletos DEBEN identificarse como parciales y mostrar su cobertura. El resumen final DEBE permanecer estable al navegar o modificar el conteo; trabajos antiguos con información insuficiente DEBEN declararlo expresamente.
- **FR-019**: La exportación solicitada DEBE mostrar en cada cuadro las cajas y sus etiquetas con clase e identificador estable, usando colores de clase consistentes y contraste legible; toda caja exportada DEBE tener su etiqueta asociada.
- **FR-020**: Las etiquetas DEBEN situarse encima de la caja cuando haya espacio, mantenerse dentro del cuadro y ajustarse en bordes/agrupaciones para reducir oclusiones y conservar la asociación; si es necesaria otra ubicación, DEBE seguir siendo inequívoca.
- **FR-021**: La descarga DEBE conservar dimensiones, cronología y velocidad de reproducción del video conforme al comportamiento vigente, sin volver a detectar/enriquecer vehículos para añadir etiquetas. Exportar DEBE seguir siendo explícito e independiente de errores de consulta de la ficha.
- **FR-022**: La solución DEBE conservar reproducción progresiva, bloqueo de zonas no analizadas, búsqueda hacia atrás, identidades locales, colores, conteo por mediciones y consulta bajo demanda; no DEBE volver a activar enriquecimiento o exportación automáticos.
- **FR-023**: Resumen, configuraciones, consultas y medios DEBEN respetar aislamiento entre trabajos/usuarios y la retirada/vencimiento existentes. La nueva iteración no DEBE ampliar la conservación de videos, recortes o placas.
- **FR-024**: La especificación, decisiones, validaciones y cambios posteriores DEBEN registrarse en la documentación de esta iteración con sus commits, distinguiendo lo implementado de las evaluaciones pendientes y conservando los cambios existentes.

### Key Entities *(include if feature involves data)*

- **Identidad de vehículo**: Trayectoria local a un video, con Track ID estable, observaciones confirmadas y clase consolidada. Su identificador no es un contador ni una garantía de reidentificación física tras perder el seguimiento.
- **Contexto de inspección**: Video, identidad e instante elegidos; determina evidencia, estado y resultados de una consulta, evitando contaminación entre consultas.
- **Evidencia de inspección**: Recorte de vehículo y placa cuando exista, con su instante real y relación con el vehículo seleccionado; permanece estable dentro del contexto consultado.
- **Configuración de conteo**: Segmento, sentido elegido, estado y versión de aplicación sobre un video; sus cambios delimitan acumulados independientes.
- **Evento de cruce**: Paso confirmado de una identidad por el segmento en el sentido configurado, con instante y pertenencia a una configuración.
- **Resumen de detecciones**: Cobertura parcial/final, total de identidades y distribución por clases; independiente de eventos de cruce.
- **Video anotado exportado**: Descarga solicitada con cajas, etiquetas, colores e identidades sincronizados, sin generar un segundo análisis.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En anchos de referencia de 360, 768 y 1440 píxeles, se puede recorrer y cerrar una ficha completa con todos sus apartados sin barra vertical independiente sobre toda la ficha, contenido inaccesible ni desplazamiento horizontal de página; coincide visualmente con la ficha de imágenes equivalente.
- **SC-002**: En el 100 % de los casos controlados de selección, respuestas retrasadas y actualización, vehículo e instante de la ficha coinciden con la selección vigente; durante 30 segundos de consulta sin cambiar la selección, los recortes ya disponibles no alternan, se vacían ni se reinician por actualizaciones periódicas.
- **SC-003**: Al consultar una identidad en dos instantes controlados con apariencia diferente, ambas consultas muestran el recorte correspondiente al instante elegido; una ausencia de placa del primer instante no impide consultar la del segundo. Reabrir el mismo contexto resuelto no vuelve a ejecutar su análisis de enriquecimiento.
- **SC-004**: En escenas controladas con cruces correctos/inversos, contactos, prolongaciones, extremos, oclusiones y cuadros predichos, el conteo coincide exactamente con los eventos elegibles observados manualmente: cero duplicados y cero aumentos por movimientos excluidos.
- **SC-005**: Tras dos recorridos de reproducción, cinco saltos hacia atrás/adelante y actualizaciones repetidas, el contador coincide con la referencia histórica en cada posición. Invertir el sentido y aplicarlo produce el acumulado esperado de la configuración nueva sin repetir el análisis de detección.
- **SC-006**: En videos controlados, el resumen final coincide con las identidades confirmadas de cada clase, la suma por clases coincide con el total y ambos resultados son iguales con conteo activado/desactivado. El caso sin vehículos muestra cero y los incompletos siempre se identifican como parciales.
- **SC-007**: En la descarga de prueba, el 100 % de las cajas dibujadas tiene etiqueta de clase/identidad correcta y sincronizada; todas las etiquetas quedan dentro del cuadro y permiten asociarlas a su vehículo, incluidos bordes y vehículos próximos.
- **SC-008**: Analizar/reproducir sin exportar ni seleccionar vehículos no inicia enriquecimientos ni generación de video anotado. Crear el resumen, recalcular cruces y exportar etiquetas aprovecha el análisis existente sin una nueva detección del video.
- **SC-009**: Selección/cierre de ficha, definición/inversión de sentido y activación/desactivación de conteo se completan mediante teclado y toque, con foco visible y nombres que distinguen identidad, cruces y total detectado.

## Assumptions

- La aclaración del usuario fija un único sentido elegido e indicado con flecha; se descarta el conteo bidireccional para esta nueva experiencia. Se cuenta el primer cruce elegible por identidad y configuración.
- Se usa el centro de la caja como referencia de cruce para mantener un criterio coherente con el comportamiento previo; se exige atravesar el segmento finito, no su prolongación.
- El término «identificador del conteo» se interpreta como un indicador numérico claro y correcto del acumulado, separado del Track ID; no implica renumerar vehículos.
- El resumen representa vehículos mediante las identidades de seguimiento confirmadas del trabajo. Mejorar reidentificación tras pérdida prolongada o entre cámaras queda fuera de esta iteración; esa limitación debe quedar visible en la documentación del resumen.
- La evidencia solicitada corresponde al contexto temporal seleccionado, no necesariamente al mejor recorte de toda la trayectoria. Cualquier alternativa por falta de evidencia requiere elección explícita y muestra el tiempo real.
- Las etiquetas exportadas contienen nombre de clase e identificador local. No se añade matrícula reconocida como etiqueta, audio nuevo ni datos inventados.
- Se conserva el aspecto profesional de imágenes, los colores sólidos por clase y la adaptación móvil; no se rediseña globalmente la marca ni se altera el flujo de imágenes.
- Se requieren las observaciones temporales, fuentes autorizadas, evidencias y capacidades de exportación existentes de la iteración 009. La planificación determinará qué contratos o datos internos deben extenderse para cumplir los requisitos, sin decisiones de implementación en esta especificación.
- La aceleración AMD/DirectML, cambio de pesos, resolución, hilos, cadencia de detección y entrenamiento quedan fuera de alcance. La creación de esta especificación no acredita pruebas de implementación ni cierra pendientes de iteraciones anteriores.

## Clarifications

### Session 2026-11-24

- Q: ¿Contar en un solo sentido elegido o en ambos dentro de un único total? → A: «Un solo sentido elegido, indicado con una flecha».
