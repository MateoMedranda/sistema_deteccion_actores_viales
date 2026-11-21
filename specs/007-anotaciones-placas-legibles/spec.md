# Feature Specification: Anotaciones despejadas y placas legibles

**Feature Branch**: `feature/007-anotaciones-placas-legibles` (activa en el checkout principal)

**Created**: 2026-11-20

**Status**: Draft — validada para planificación

**Input**: En la siguiente iteración, impedir que los números de detección tapen los autos del fondo, distinguir los recuadros por clase y mejorar la visualización de placas y la exactitud de su lectura.

**Reference**: [006-mejoras-frontend](../006-mejoras-frontend/spec.md). Captura aportada por el usuario: escena de 4032 × 1908 con 21 detecciones, identificadores superpuestos y algunos números partidos en varias líneas.

**Contexto de trabajo**: Especificación creada en el checkout principal, conservando `feature/006-mejoras-frontend` y sus cambios existentes. El directorio 007 es independiente de la rama actual. Este documento no crea ni cambia ramas ni implementa modificaciones.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Explorar vehículos sin que los números oculten la escena (Priority: P1)

Como usuario, quiero reconocer y seleccionar vehículos cercanos y lejanos sin que sus identificadores tapen la imagen, para explorar escenas con tráfico denso.

**Why this priority**: La captura muestra que la numeración impide ver precisamente los vehículos pequeños que se necesita inspeccionar.

**Independent Test**: Abrir una escena densa con al menos 21 detecciones, recorrer vehículos por puntero, teclado y toque, y comprobar que no hay bloques de numeración sobre la imagen ni pérdida de correspondencia con la ficha.

**Acceptance Scenarios**:

1. **Given** una escena analizada con vehículos próximos y lejanos, **When** se muestra por primera vez, **Then** se ven los contornos y ninguna etiqueta numérica permanente se superpone a la escena.
2. **Given** una detección elegible, **When** recibe puntero, foco o selección, **Then** su identificador y clase se muestran completos en una zona de contexto fuera de la imagen; el contorno comunica el estado y no aparece otro bloque sobre los vehículos.
3. **Given** una detección seleccionada y otra bajo el puntero o foco, **When** cambia el contexto transitorio, **Then** la ficha conserva su selección hasta una activación explícita y la zona de contexto identifica inequívocamente qué detección describe.
4. **Given** cajas pequeñas o solapadas y un dispositivo táctil, **When** se utiliza la lista equivalente, **Then** cualquier vehículo elegible se selecciona sin depender de pasar el ratón ni ampliar su zona activa sobre otro vehículo.
5. **Given** identificadores de una, dos o tres cifras, **When** cambia el ancho de pantalla o se amplía el texto al 200%, **Then** cada identificador permanece en una sola línea y ningún texto esencial sale de su contenedor.
6. **Given** una imagen que ya contiene textos de anotación del servicio, **When** se presenta la nueva exploración, **Then** esos textos tampoco ocultan la escena: el resultado visible cumple el modo despejado completo, sin limitarse a esconder una segunda capa de etiquetas.

---

### User Story 2 - Reconocer las clases mediante colores consistentes (Priority: P1)

Como usuario, quiero distinguir las clases de actores viales por el color de sus contornos y una leyenda clara, para interpretar rápidamente la escena.

**Why this priority**: Los contornos uniformes actuales no permiten reconocer la clase de un vehículo antes de abrir su ficha.

**Independent Test**: Mostrar una escena con todas las clases viales configuradas y comprobar que el color y el nombre de cada clase son consistentes en la escena, leyenda, lista y detalle.

**Acceptance Scenarios**:

1. **Given** varias clases conocidas, **When** se dibujan sus recuadros, **Then** cada clase tiene un color sólido distinto y estable; dos vehículos de la misma clase comparten color.
2. **Given** una selección o foco sobre un contorno, **When** cambia su estado, **Then** la clase sigue reconocible y el estado se distingue mediante un indicador adicional al color.
3. **Given** una persona que no distingue algunos colores o un fondo muy claro u oscuro, **When** consulta la leyenda, el contexto o la lista, **Then** puede conocer la clase y encontrar el foco sin depender exclusivamente del color.
4. **Given** una clase desconocida o no enriquecible, **When** aparece en la escena, **Then** se representa con nombre y tratamiento alternativo explícitos; no se inventa una clase ni se ofrece una ficha vehicular inexistente.

---

### User Story 3 - Inspeccionar la placa original y una versión procesada (Priority: P1)

Como usuario autorizado, quiero ampliar y comparar el recorte original de una placa con una versión procesada, para revisar su legibilidad sin confundir un tratamiento visual con la evidencia original.

**Why this priority**: Una imagen aparentemente más nítida debe seguir siendo comprobable y corresponder a la misma placa.

**Independent Test**: Seleccionar vehículos con placa legible, ilegible, ausente y fallida; comparar las vistas cuando hay localización válida y comprobar identidad, procedencia, estados y retirada de evidencia.

**Acceptance Scenarios**:

1. **Given** una placa localizada con evidencia vigente, **When** se abre su ficha, **Then** el original está disponible y la versión procesada se prepara sin exigir volver a analizar la escena; ambas están identificadas y pueden compararse con el mismo vehículo seleccionado.
2. **Given** las dos versiones disponibles, **When** se alternan o amplían, **Then** se conserva su relación geométrica y se distingue qué tratamiento visual se aplicó; una ampliación no se presenta como aumento comprobado de detalle capturado.
3. **Given** una placa localizada pero ilegible, **When** se solicita su visualización, **Then** el recorte puede inspeccionarse y procesarse aunque no haya texto reconocido; la interfaz conserva el estado de lectura que corresponda.
4. **Given** falta de localización fiable o de original autorizado, **When** se abre la sección, **Then** se explica por qué no hay versión procesada y no se estima una placa ni se utiliza otra detección.
5. **Given** fallo, plazo agotado o tratamiento no aplicable, **When** termina el intento, **Then** el original válido sigue visible y se muestra un estado comprensible sin espera indefinida.
6. **Given** cambio de vehículo, fuente, credencial, reinicio o vencimiento, **When** una transformación anterior termina tarde, **Then** no restaura evidencia descartada ni aparece en la nueva ficha.

---

### User Story 4 - Mejorar la lectura automática con evidencia medible (Priority: P2)

Como usuario, quiero que el tratamiento de placas permita lecturas más exactas cuando la imagen contiene información suficiente, sin aumentar las lecturas falsas ni alterar los resultados solo para hacerlos parecer más seguros.

**Why this priority**: La exactitud requiere medición con texto de referencia; la apariencia y la confianza del lector por sí solas no la demuestran.

**Independent Test**: Comparar el comportamiento vigente y los tratamientos candidatos sobre un conjunto reservado de placas con texto verificado, usando las mismas imágenes, modelos, umbrales y condiciones; registrar aciertos completos, errores por carácter, lecturas equivocadas aceptadas y coste de procesamiento.

**Acceptance Scenarios**:

1. **Given** placas con bajo contraste, ruido, inclinación o tamaño reducido que conservan información útil, **When** se evalúa una estrategia candidata, **Then** se compara con el comportamiento actual completo, incluido su reintento de mejora existente, sin presentar esa capacidad previa como nueva.
2. **Given** una lectura final basada en alguna variante, **When** se consulta su procedencia, **Then** se distingue si se intentó un tratamiento, cuál se utilizó para el texto publicado y cuál versión se muestra para inspección.
3. **Given** candidatos que producen textos distintos, confianza alta con texto incorrecto o información insuficiente, **When** se decide la lectura final, **Then** se aplica una regla documentada y validada; no se elevan estados o confianzas artificialmente ni se inventan caracteres.
4. **Given** una estrategia que no supera los criterios de exactitud o aumenta lecturas falsas, **When** finaliza su evaluación, **Then** no sustituye el comportamiento vigente para lectura automática y la limitación se registra; su eventual uso exclusivamente visual sigue identificado como tal.

### Edge Cases

- Vehículos del fondo con cajas diminutas, grupos densos, cajas superpuestas e identificadores largos.
- Una detección en el borde de la imagen; puntero o foco en una distinta de la selección activa.
- Escena con cero detecciones o solo actores no elegibles; clase nueva o nombre no traducido.
- Numeración ya integrada en la imagen recibida, además de controles interactivos visibles.
- Texto al 200%, pantallas de 360, 768 y 1440 píxeles, toque, teclado y movimiento reducido.
- Placa de pocos píxeles, borrosa, inclinada, parcialmente ocluida, saturada o con reflejos; el tratamiento puede no ayudar o empeorarla.
- Localización errónea, recorte fuera de límites, orientación reflejada/rotada o evidencia sin correspondencia.
- Conflicto entre lectura original y procesada; mayor confianza que no corresponde a un mayor acierto.
- Cambio de selección durante procesamiento, respuestas tardías, error, cancelación y vencimiento.
- Conjunto sin degradaciones relevantes o línea base ya perfecta; no se fabrica una ganancia para superar la evaluación.
- Falta de medios privados, referencias verificadas o recursos de evaluación; aceptación pendiente, nunca reemplazada por resultados sintéticos de exactitud.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: La exploración de imágenes MUST abrir con contornos sin etiquetas numéricas permanentes sobre los píxeles de la escena. La solución abarcará cualquier texto de anotación ya integrado en la imagen mostrada.
- **FR-002**: La identificación contextual MUST aparecer fuera del área de imagen y describir una sola detección a la vez, con prioridad de foco, después puntero y después selección. Indicará identificador y clase completos, sin partir cifras.
- **FR-003**: Puntero y foco MUST destacar la detección contextual sin cambiar por sí solos la selección ni la ficha. Al terminar el contexto transitorio se recuperará la identificación de la selección vigente.
- **FR-004**: La selección y asociación entre escena, lista, ficha y recortes MUST conservar la identidad de fuente/detección; seguirá funcionando por clic, toque y teclado, con lista equivalente para cajas pequeñas o solapadas y sin ampliar cajas sobre otras detecciones.
- **FR-005**: Cada clase vial conocida y configurada MUST tener un color sólido propio, estable entre análisis y coherente en escena, lista, leyenda y ficha. La clase desconocida tendrá un tratamiento alternativo explícito con su nombre disponible.
- **FR-006**: Una leyenda MUST relacionar colores y nombres de las clases presentes. Los actores no enriquecibles se conservarán sin aparentar que admiten enriquecimiento vehicular.
- **FR-007**: Los estados de foco, paso del puntero y selección MUST distinguirse entre sí y preservar el reconocimiento de clase mediante texto o forma además de color. Se mantendrán contraste mínimo 4.5:1 para texto y 3:1 para controles/foco sobre fondos claros y oscuros; los controles principales y equivalentes tendrán un mínimo de 44 × 44 píxeles.
- **FR-008**: La distribución MUST funcionar a anchos de 360, 768 y 1440 píxeles y con texto al 200%, sin desplazamiento horizontal de toda la página, identificadores partidos ni acciones esenciales recortadas.
- **FR-009**: Una placa seleccionada con localización fiable, original autorizado y vigencia válida MUST permitir obtener una versión procesada para inspección, sin repetir detección ni exigir un segundo análisis general.
- **FR-010**: La interfaz MUST conservar acceso al recorte original fiel, etiquetar la versión procesada y permitir comparación y ampliación con proporción preservada. Ninguna versión procesada sustituirá silenciosamente la evidencia original.
- **FR-011**: El tratamiento MUST limitarse a transformar información de la misma región de placa, preservando procedencia y asociación. No generará caracteres, completará partes ocultas ni reconstruirá detalles plausibles como evidencia. Si la imagen no permite mejorar, se declarará esa limitación.
- **FR-012**: La disponibilidad de visualización procesada MUST ser independiente del éxito de la lectura: una placa localizada e ilegible podrá mostrarse; una ausente o sin localización fiable no recibirá un recorte estimado.
- **FR-013**: La versión procesada MUST tener estados de preparación, disponible, no aplicable, fallo y vencimiento comprensibles. Un fallo no eliminará el original vigente ni mantendrá una espera indefinida; el usuario podrá recuperar solo el tratamiento afectado cuando proceda.
- **FR-014**: La procedencia MUST diferenciar tratamiento intentado, variante que originó la lectura final y variante mostrada. La interfaz no confundirá una mejora visual con un nuevo resultado de lectura ni cambiará la lectura publicada por alternar vistas.
- **FR-015**: La mejora de lectura automática MUST evaluarse contra el recorrido vigente completo, usando texto de referencia verificado y separación entre material de ajuste y material de evaluación. Se medirán coincidencia completa de placa, error por carácter y lecturas equivocadas aceptadas; subir la confianza no demuestra mayor exactitud.
- **FR-016**: Solo una estrategia que supere SC-006 MUST poder sustituir el comportamiento vigente de lectura en esta iteración. Si no lo supera, se conservará la lectura actual y se documentará el objetivo pendiente; no se afirmará que la exactitud mejoró.
- **FR-017**: Las placas originales, versiones procesadas y lecturas MUST conservar la autorización, propietario y menor vigencia aplicable. Reset, cambio de identidad/fuente, vencimiento o rechazo de acceso retirarán toda evidencia afectada; ninguna respuesta tardía podrá restaurarla.
- **FR-018**: El tratamiento MUST ejecutarse sin bloquear innecesariamente las demás operaciones ni duplicar trabajos por selección repetida o cambio de vista. Las versiones no ampliarán la retención ni añadirán historial o exportación; no se enviarán placas a terceros.
- **FR-019**: La evaluación MUST registrar condiciones reproducibles, duración, memoria y resultado seguros del procesamiento, sin incluir imágenes, texto de placas, credenciales ni rutas privadas en registros o informes públicos.
- **FR-020**: Se MUST conservar el análisis/enriquecimiento en una acción, asociación y geometría de 006, estados independientes, accesibilidad, limpieza, video y conteo existentes. No se cambiarán autenticación, clases detectadas, modelos, pesos ni umbrales; el rediseño de video y el seguimiento real en imágenes permanecen fuera del alcance.

### Key Entities *(include if feature involves data)*

- **Clase visual**: Clase vial recibida y su nombre, color estable y representación accesible.
- **Detección contextual**: Detección bajo foco o puntero, o la seleccionada cuando no hay interacción transitoria; no implica una nueva selección ni modifica su identidad.
- **Evidencia original de placa**: Región fiel y autorizada de la misma fuente y vehículo, con localización y vigencia verificables.
- **Versión procesada**: Derivada temporal de esa evidencia, con tratamiento, estado y procedencia; se distingue del original y no añade información observada.
- **Resultado de lectura**: Texto y estado autorizados, confianza recibida y variante de origen; no depende de qué vista de comparación esté abierta.
- **Evaluación comparativa**: Conjuntos separados de ajuste/evaluación, referencias verificadas, línea base, resultados agregados y condiciones reproducibles.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En al menos 10 escenas controladas, incluidas 3 con 21 o más detecciones y cajas de fondo pequeñas/solapadas, el 100% de vistas en 360/768/1440 píxeles muestra cero etiquetas identificadoras sobre la imagen en modo inicial y durante interacción; la zona externa describe como máximo una detección sin partir su identificador, también con texto al 200%.
- **SC-002**: El 100% de detecciones elegibles del conjunto controlado se selecciona por su identidad correcta desde escena o lista; teclado y toque cubren cajas pequeñas/solapadas. Con datos ya cargados, el cambio de contexto y ficha aparece en menos de 1 segundo en el dispositivo documentado.
- **SC-003**: El 100% de clases conocidas configuradas supera una matriz de representación: color propio estable, leyenda/nombre coherentes y estados distinguibles sin depender solo de color; revisión registrada de contraste sobre fondos claros/oscuros y sin regresión del foco o de los controles equivalentes.
- **SC-004**: En al menos 30 placas con localización válida, el 100% de comparaciones original/procesada conserva fuente, vehículo, región, etiquetas de procedencia y vigencia; los casos sin evidencia válida muestran indisponibilidad explícita, nunca otra placa ni un recorte estimado.
- **SC-005**: El 100% de pruebas de fallo, límite de espera, cambio de selección, reset, rechazo y vencimiento conserva el original cuando sigue autorizado y retira las versiones que dejan de estarlo; ninguna respuesta tardía restaura datos. Las pruebas de regresión de imagen, video y conteo pertinentes siguen pasando.
- **SC-006**: Sobre un conjunto de evaluación reservado de al menos 60 placas con texto verificado (al menos 30 degradadas con referencia y 30 de control), la estrategia candidata aumenta en al menos 5 puntos porcentuales la coincidencia completa en el subconjunto degradado, no reduce la coincidencia global ni aumenta el número de lecturas equivocadas aceptadas frente a la línea base vigente. Tampoco aumenta el error global por carácter, definido como inserciones, eliminaciones y sustituciones divididas por caracteres de referencia. Se utilizan las mismas fuentes, modelos, umbrales, normalización de texto y condiciones, fijados antes de evaluar. Ninguna imagen del conjunto reservado se usa para ajustar el tratamiento.
- **SC-007**: En el dispositivo y condiciones documentados, la preparación de la versión procesada de una placa seleccionada termina en un máximo de 2 segundos en al menos el 95% de las 30 placas de SC-004; todos los intentos terminan en un estado explícito en un máximo de 10 segundos o antes si vence el acceso. El coste adicional de la lectura automática se registra aparte y no se oculta dentro de esta medición visual.
- **SC-008**: El 100% de los casos controlados de procesamiento y cancelación/vencimiento genera mediciones correlacionadas de duración, memoria y desenlace; la inspección de registros confirma ausencia de evidencia sensible. La limpieza de derivados vencidos mantiene el margen máximo de 2 segundos con el servicio activo.
- **SC-009**: La entrega incluye una comparación agregada de exactitud y coste con línea base, hardware y configuración documentados. Si faltan referencias o no se supera SC-006, el objetivo de exactitud permanece explícitamente pendiente; una demostración visual o un conjunto sintético no se utiliza como sustituto de esa aceptación.

## Assumptions

- La iteración se centra en imágenes. Mantiene video/conteo y su apariencia compartida sin rediseñar su exploración.
- La identificación completa se traslada fuera de la escena; no se incorpora una vista con todos los números superpuestos ni se reduce su tamaño hasta volverlos ilegibles.
- Se mantienen colores sólidos y presentación formal de 006. El color expresa clase, no identidad individual ni estado de lectura.
- El usuario autoriza planificar los cambios de presentación y procesamiento de placas necesarios en frontend y backend. Esta fase solo produce especificación; la elección de algoritmos, contratos, reparto de procesamiento y límites de recursos corresponde al plan.
- La mejora visual se entiende como un tratamiento conservador y verificable. No se incluye reconstrucción generativa, sustitución por modelos nuevos ni entrenamiento de pesos.
- 006 conserva el recorte original sin alterar. 007 añade una derivada explícitamente identificada como procesada y nunca reinterpreta el significado de la evidencia original ni modifica las especificaciones históricas.
- El comportamiento vigente ya incluye un intento de mejora para algunas lecturas débiles. La línea base de esta iteración incluye ese recorrido; no se declara como nueva una capacidad ya existente.
- Una transformación puede facilitar inspección y lectura, pero no garantiza recuperar caracteres ausentes o demasiado degradados. La captura aportada ilustra el problema de presentación y no constituye un conjunto de referencia para evaluar placas.
- Los objetivos numéricos de esta especificación son criterios futuros, no resultados ya obtenidos. Los medios deben ser controlados y autorizados, con referencias privadas verificadas y un conjunto de ajuste distinto del reservado.
- Se conservan las protecciones de sesión, acceso y privacidad de 006. No se añade historial, exportación, consultas a registros de vehículos ni servicios externos que reciban imágenes.
- Los pendientes T067/T068 de 006 no se trasladan ni se dan por cerrados al abrir 007; su aceptación se mantiene separada. La disponibilidad de referencias para SC-006 y del entorno de evaluación es una dependencia para acreditar mayor exactitud.
- El trabajo de 007 continúa en el checkout principal sobre `feature/007-anotaciones-placas-legibles`, preservando los cambios existentes, sin sobrescribir archivos ajenos ni mezclar los cierres de aceptación de otras iteraciones.
