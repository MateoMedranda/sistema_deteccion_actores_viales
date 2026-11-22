# Feature Specification: Exploración de imágenes y video

**Feature Branch**: `feature/008-exploracion-imagen-video`

**Created**: 2026-11-21

**Status**: Draft — validada para planificación

**Input**: Nueva iteración para seleccionar Imagen o Video desde un menú superior; configurar URL del backend y API key mediante variables de entorno; ampliar y recorrer la escena original; mejorar presentación, precisión temporal y fluidez de las cajas en video sin perder rendimiento; automatizar su enriquecimiento y mostrar progreso de ambas etapas. Entregar una propuesta para consultar datos de vehículos durante la reproducción. Crear rama y hacer commit al completar cada etapa.

**Reference**: [006-mejoras-frontend](../006-mejoras-frontend/spec.md) y [007-anotaciones-placas-legibles](../007-anotaciones-placas-legibles/spec.md). La captura aportada muestra el formulario de configuración de sesión sobre el análisis de imágenes y el video relegado a herramientas secundarias.

**Contexto de trabajo**: Checkout principal; nueva rama derivada del estado actual con las correcciones de007. Esta etapa crea especificación y documentación, sin implementar el producto ni modificar archivos existentes ajenos a ella.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Elegir Imagen o Video desde la navegación principal (Priority: P1)

Como usuario, quiero elegir el tipo de análisis en la parte superior y encontrar un espacio de trabajo claro para cada uno.

**Why this priority**: Video debe tener la misma visibilidad que Imagen, sin depender de desplegar herramientas secundarias.

**Independent Test**: Recorrer ambos modos en móvil, tablet y escritorio, también con teclado y texto al200%; verificar que cambiar de modo conserva el trabajo vigente y no inicia operaciones adicionales.

**Acceptance Scenarios**:

1. **Given** la aplicación abierta, **When** se consulta la cabecera, **Then** Imagen y Video están disponibles, el modo activo es inequívoco y solo su espacio de trabajo ocupa el área principal.
2. **Given** una imagen o un video en procesamiento, **When** se cambia al otro modo y se vuelve, **Then** su estado y resultados vigentes se conservan; no se cancela, duplica ni reinicia el trabajo por navegar.
3. **Given** un dispositivo táctil o navegación por teclado, **When** se cambia de modo, **Then** los controles son alcanzables, el foco es visible y no aparecen acciones esenciales recortadas.
4. **Given** una evidencia que vence mientras su modo está oculto, **When** se vuelve a ese modo, **Then** la evidencia ya está retirada y el estado explica su indisponibilidad.

---

### User Story 2 - Empezar con la conexión configurada por entorno (Priority: P1)

Como operador, quiero configurar la URL del servicio y su API key en el entorno de despliegue para que el usuario analice archivos sin introducir datos de conexión.

**Why this priority**: La configuración técnica no debe interrumpir el flujo habitual ni convertir una credencial privada en información del navegador.

**Independent Test**: Abrir la aplicación con configuración válida, ausente e inválida; verificar preparación y errores seguros, sin formulario obligatorio ni exposición de la credencial.

**Acceptance Scenarios**:

1. **Given** URL y credencial válidas configuradas por el operador, **When** se abre la aplicación, **Then** se puede seleccionar un medio sin copiar una clave ni editar la URL en la pantalla.
2. **Given** una configuración ausente, inválida o un servicio no disponible, **When** se intenta iniciar, **Then** se informa el estado de conexión sin divulgar valores secretos ni enviar archivos a un destino alternativo.
3. **Given** la aplicación entregada al usuario, **When** se inspeccionan contenidos, descargas y comunicaciones accesibles desde el navegador, **Then** la API key del backend no aparece como dato recuperable.
4. **Given** un reinicio de sesión o rechazo de acceso, **When** se actualiza la pantalla, **Then** se retira la evidencia afectada y se conserva la configuración administrada; no se convierte el acceso al backend en acceso anónimo.

---

### User Story 3 - Ampliar y recorrer la escena original (Priority: P2)

Como usuario, quiero hacer zoom sobre la imagen grande para inspeccionar vehículos del fondo sin perder correspondencia entre contornos y fichas.

**Why this priority**: Las placas ya pueden ampliarse; falta explorar la escena completa y las cajas pequeñas.

**Independent Test**: Ampliar, desplazar, seleccionar y restablecer una escena densa; verificar geometría e identidad de los mismos vehículos antes y después.

**Acceptance Scenarios**:

1. **Given** una escena original cargada, **When** se acerca, aleja o ajusta a la vista, **Then** la imagen y sus contornos cambian juntos, se conserva la proporción y se indica el nivel de ampliación.
2. **Given** una escena ampliada, **When** se arrastra o utiliza un control equivalente, **Then** puede recorrerse toda la imagen sin desplazar horizontalmente la página; arrastrar no selecciona accidentalmente otro vehículo.
3. **Given** un vehículo pequeño o superpuesto, **When** se selecciona desde la escena ampliada o su lista equivalente, **Then** se abre la misma ficha correcta y no cambia el original ni sus recortes.
4. **Given** una selección activa, **When** se modifica el zoom o se restablece el encuadre, **Then** no se repiten detección, enriquecimiento o lectura y no aparecen números sobre la escena.

---

### User Story 4 - Ver video con contornos claros, precisos y fluidos (Priority: P1)

Como usuario, quiero un video con contornos por clase coherentes con las imágenes, sin rótulos que oculten vehículos y sin oscilaciones visuales innecesarias.

**Why this priority**: La presentación actual de video incorpora textos y cajas uniformes; mejorar su apariencia no debe desalinear las detecciones ni perjudicar el procesamiento.

**Independent Test**: Comparar la presentación vigente y la nueva sobre clips controlados con tráfico denso, movimiento rápido, cruces, oclusiones y cambios de escena, manteniendo el mismo entorno y procesamiento aprobado.

**Acceptance Scenarios**:

1. **Given** un video con varias clases, **When** se reproduce el resultado, **Then** las cajas usan colores sólidos y nombres coherentes con Imagen; su identificación completa está fuera de los píxeles del video.
2. **Given** un vehículo en movimiento, **When** avanza la reproducción, **Then** el contorno corresponde a ese vehículo en ese instante y no queda retrasado, adelantado o unido al de otro vehículo para parecer más suave.
3. **Given** pérdida del seguimiento, oclusión, salida o cambio de escena, **When** dejan de existir observaciones válidas para un contorno, **Then** no permanece una caja inventada ni se reutiliza su enriquecimiento para otra identidad.
4. **Given** el mismo video en distintos tamaños o pantalla completa, **When** cambia su presentación, **Then** se conservan proporción, alineación, duración y correspondencia temporal.
5. **Given** las mismas fuentes y condiciones, **When** se mide la nueva presentación, **Then** se acredita su fluidez y coste contra una línea base; no se ocultan regresiones reduciendo la calidad o cantidad de video procesado.

---

### User Story 5 - Analizar y enriquecer un video con progreso claro (Priority: P1)

Como usuario, quiero iniciar el análisis una sola vez y saber cuánto falta en procesamiento y enriquecimiento, pudiendo aprovechar el video aunque alguna lectura falle.

**Why this priority**: Hoy procesamiento y enriquecimiento son acciones separadas y la salida de enriquecimiento no está presentada para una consulta habitual.

**Independent Test**: Iniciar un video, observar ambas etapas y consultar resultados; repetir con ausencia de vehículos, fallos, cancelación, interrupción y vencimiento.

**Acceptance Scenarios**:

1. **Given** un video válido, **When** se inicia su análisis, **Then** se procesa y su enriquecimiento elegible se inicia automáticamente cuando la fuente está lista, sin una segunda acción de análisis.
2. **Given** un trabajo en cola, procesamiento, preparación del resultado o enriquecimiento, **When** se consulta el progreso, **Then** cada etapa indica su estado real y sus unidades disponibles; no se anuncia como completada una etapa todavía activa.
3. **Given** un video ya disponible y enriquecimiento en curso, **When** se reproduce el resultado, **Then** puede verse sin esperar todas las lecturas, con el progreso de enriquecimiento todavía visible.
4. **Given** un fallo de enriquecimiento o de un atributo, **When** termina esa operación, **Then** el video vigente sigue disponible, se distingue el resultado parcial y la recuperación no repite una detección ya terminada innecesariamente.
5. **Given** un video sin vehículos elegibles, **When** termina el procesamiento, **Then** se informa que el enriquecimiento no aplica, sin porcentajes ficticios ni espera indefinida.
6. **Given** cancelación, cambio explícito de archivo, rechazo de acceso o vencimiento, **When** llega una respuesta anterior, **Then** no restaura resultados descartados ni vincula datos al nuevo video.

---

### User Story 6 - Consultar los vehículos enriquecidos y definir su futura inspección en video (Priority: P2)

Como usuario, quiero consultar resultados de video por track ID con una presentación legible y recibir una propuesta concreta para inspeccionarlos dentro de la reproducción.

**Why this priority**: El enriquecimiento debe ser utilizable ahora; la interacción temporal precisa sobre el reproductor necesita un alcance explícito.

**Independent Test**: Consultar la lista de vehículos de un video con varios resultados y revisar la propuesta de pausa/selección con sus dependencias.

**Acceptance Scenarios**:

1. **Given** resultados autorizados, **When** se abre un vehículo desde la lista de video, **Then** se muestran su track ID real, clase, atributos, estado de placa y procedencia disponible, sin una salida técnica como presentación principal.
2. **Given** más vehículos de los que caben en una página, **When** se recorre la lista, **Then** todos los resultados autorizados son accesibles, sin truncamiento silencioso ni mezcla de trabajos.
3. **Given** evidencia referida a un cuadro o instante representativo, **When** se consulta la ficha, **Then** esa referencia se distingue de la posición actual de reproducción y no se finge que la lectura se actualiza en cada cuadro.
4. **Given** el cierre de la iteración, **When** se entrega su documentación, **Then** contiene una propuesta revisada para pausar, seleccionar un vehículo del instante visible y abrir una ficha, con alternativa de lista, estados sin datos y dependencias para una iteración posterior.

### Edge Cases

- Cambio entre modos mientras hay trabajos activos, errores de conexión o evidencia que vence en segundo plano.
- Configuración de entorno ausente, URL inválida, credencial revocada, reinicio y servicio parcialmente disponible.
- Intento de recuperar la credencial desde contenido entregado, registros, mensajes o configuración accesible al navegador.
- Imagen muy ancha/alta, orientación canónica, cajas diminutas o superpuestas, ampliación máxima, arrastre frente a clic, toque y teclado.
- Video con movimiento rápido, cámaras móviles, oclusiones, cruces, entrada/salida, cambio de escena o intervalos sin detecciones.
- Cambio de tamaño, relación de aspecto, giro, búsqueda temporal, pausa y pantalla completa; valores de duración o cuadros todavía no confirmados.
- Trabajo en cola o preparando el archivo final; una etapa termina mientras otra sigue pendiente.
- Cero vehículos elegibles, muchas identidades, resultados paginados, placa ausente o ilegible y atributos parciales.
- Cancelación durante procesamiento o enriquecimiento, reintento, respuesta tardía, memoria agotada o acceso vencido.
- Pérdida de identidad del seguimiento: no resolverla inventando continuidad visual o adjudicando datos de otro vehículo.
- Conteo por línea activo sobre un video; cambios de presentación no alteran su geometría ni sus resultados.
- Línea base ya fluida o fuentes sin oscilación medible; no fabricar una ganancia ni modificar referencias después de medir.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: La navegación superior MUST ofrecer Imagen y Video, con modo activo identificado y un solo espacio principal visible. Imagen será el modo inicial.
- **FR-002**: Cambiar de modo MUST conservar el estado vigente de cada espacio sin iniciar, duplicar, reiniciar o cancelar trabajos por sí solo. La conservación no crea historial ni amplía retención.
- **FR-003**: Ambos espacios MUST mantener una presentación formal de colores sólidos, jerarquía coherente, foco visible y funcionamiento en360/768/1440 y texto200%; controles principales y equivalentes de al menos44×44.
- **FR-004**: URL del backend y API key MUST proceder de variables de entorno administradas por el operador. El uso habitual no requerirá introducirlas ni mostrará un formulario de configuración técnica como paso previo.
- **FR-005**: La API key del backend MUST permanecer en un entorno de confianza y no incorporarse a contenido, configuración o comunicaciones recuperables desde el navegador, ni al repositorio o registros. Se documentará una configuración de ejemplo sin credenciales reales.
- **FR-006**: La conexión MUST distinguir preparación, configuración ausente/inválida, indisponibilidad y rechazo de acceso mediante mensajes seguros. No habrá destino alternativo, operación anónima ni envío de secretos a destinos no autorizados.
- **FR-007**: La configuración por entorno MUST conservar autenticación, autorización y asociación con el propietario vigentes. Reiniciar la sesión retirará resultados del usuario sin borrar la configuración administrada ni volver público el acceso al servicio.
- **FR-008**: La escena original de Imagen MUST poder acercarse, alejarse, ajustarse al contenedor y restablecerse, mostrando la escala. Se permitirá inspeccionar hasta400% y recorrer las zonas que queden fuera del encuadre.
- **FR-009**: El desplazamiento de la escena MUST disponer de alternativas de teclado y toque, respetar los límites de la imagen y distinguir arrastre de activación. La página completa no tendrá desplazamiento horizontal por el zoom.
- **FR-010**: Imagen, contornos y selección MUST compartir la misma transformación visual, conservando geometría, identidad, proporción, lista equivalente y recortes originales de006/007. No reaparecerán etiquetas sobre la escena.
- **FR-011**: Zoom, desplazamiento y restablecimiento MUST ser operaciones de presentación: no repiten análisis/enriquecimiento, no modifican evidencia ni inventan detalle, y no renuevan su vigencia.
- **FR-012**: Las anotaciones de Video MUST emplear el catálogo de colores sólidos y nombres de007 para todas las clases presentes, con leyenda externa de clases, indicador de clase desconocida y aviso general de que solo vehículos elegibles según el servidor reciben enriquecimiento. El aviso cubre clases no enriquecibles sin atribuir elegibilidad individual por nombre/color. No habrá números, textos o glifos identificadores sobre los píxeles del video.
- **FR-013**: Cada contorno de Video MUST corresponder a su fuente, cuadro/instante y track ID reales, preservando alineación al redimensionar o reproducir. No se confundirá track ID con posición de lista ni con identidad real garantizada de un vehículo.
- **FR-014**: La estabilización visual MUST reducir oscilaciones innecesarias sin arrastrar cajas entre identidades, cambios de escena o intervalos sin respaldo del seguimiento. Solo afecta la representación; no reescribe observaciones, asociaciones o geometría utilizada para conteo/enriquecimiento.
- **FR-015**: La mejora de video MUST conservar el procesamiento aprobado y acreditar su coste frente a una línea base congelada. No se reducirán cuadros, resolución, duración o frecuencia presentada para ocultar regresiones, ni se cargarán modelos o repetirán inferencias por acciones de reproducción.
- **FR-016**: Analizar Video MUST encadenar automáticamente procesamiento y enriquecimiento cuando exista una fuente terminada, vigente y con vehículos elegibles. La misma operación no se iniciará dos veces por navegación, sondeo o respuestas repetidas.
- **FR-017**: La pantalla MUST mostrar progreso independiente de procesamiento y enriquecimiento, con sus estados de espera, ejecución, finalización y fallo. Porcentajes y conteos procederán de trabajo real; preparación del resultado no será presentada como finalizada y un total aún desconocido no tendrá porcentaje inventado.
- **FR-018**: El enriquecimiento de video MUST reutilizar las identidades y evidencia autorizada del seguimiento existente, con trabajo acotado por vehículo según límites vigentes; no ejecutará de nuevo detección general ni OCR por cada cuadro de reproducción.
- **FR-019**: Fallos, cancelación y recuperación MUST distinguir la etapa afectada. Un fallo de enriquecimiento no retira el video autorizado; el reintento conserva procesamiento válido cuando sea reutilizable y no inicia trabajos ilimitados. Sin elegibles se informa no aplicable.
- **FR-020**: El video terminado MUST poder reproducirse aunque el enriquecimiento siga activo o termine parcialmente; ambos estados se mostrarán sin confundir disponibilidad del medio con éxito de todas las lecturas.
- **FR-021**: El enriquecimiento de Video MUST ofrecer una lista y ficha legibles por track ID con todos los resultados autorizados accesibles. Mostrará clase, atributos, estado/texto/confianza de placa y evidencia/procedencia únicamente cuando estén disponibles, sin inventar campos ni usar datos técnicos sin presentar como vista principal.
- **FR-022**: Una referencia de cuadro/instante de evidencia MUST identificarse como observación representativa, separada del tiempo actual de reproducción. Ni un cambio de vista ni una búsqueda temporal modifican la lectura publicada.
- **FR-023**: Video MUST conservar controles normales de pausa, reproducción y búsqueda, además del conteo por línea y las capacidades previas. Se mantendrán identidad de fuente, orientación y geometría del conteo sin reutilizar una línea de otro video.
- **FR-024**: Ambas vistas y sus trabajos MUST respetar la menor vigencia aplicable, retirada por rechazo, reinicio y cambio explícito de fuente, incluso ocultas. Se cancelarán consumos obsoletos y ninguna respuesta tardía restaurará evidencia descartada.
- **FR-025**: El cierre MUST entregar una propuesta de inspección temporal de enriquecimiento: pausar, identificar vehículos del instante, seleccionar desde contorno o lista y consultar ficha con evidencia fechada. Indicará accesibilidad, ausencia de datos y dependencias; esta iteración no incluye implementar selección interactiva sobre los contornos del video.
- **FR-026**: Se MUST preservar análisis/enriquecimiento de imágenes, perfiles de placas, contratos vigentes y limpieza de006/007. No se cambiarán modelos, pesos, clases detectadas, umbrales, política OCR activa o autenticación del backend; no se añaden fuentes en vivo, entrenamiento, identificación personal ni historial.
- **FR-027**: Las mediciones MUST registrar fuentes controladas, condiciones, dispositivos efectivos, versiones, tiempos por etapa y memoria de forma reproducible y agregada, sin medios privados, textos de placas, credenciales ni rutas privadas en informes públicos. El coste nuevo del enriquecimiento se distinguirá del de presentación/procesamiento.
- **FR-028**: La entrega MUST demostrar los flujos de imagen y video, sus casos de error/acceso, no exposición de secretos, precisión visual/temporal y conservación de conteo/enriquecimiento anteriores; no se declarará mejor exactitud OCR por mejorar la interfaz.

### Key Entities *(include if feature involves data)*

- **Modo de trabajo**: Imagen o Video, espacio activo y estado vigente independiente, sin historial adicional.
- **Configuración administrada**: Dirección del servicio, credencial protegida y estado de disponibilidad, separados de los datos del usuario.
- **Vista de escena ampliada**: Original autorizado, escala, encuadre y geometría compartida con sus detecciones.
- **Trayectoria de video**: Identidad local de seguimiento, observaciones por cuadro/instante, clase y vigencia; no equivale a identidad personal persistente.
- **Contorno presentado**: Representación de una observación autorizada, con clase, geometría y correspondencia temporal comprobables.
- **Ejecución de video**: Fuente y estados correlacionados de procesamiento y enriquecimiento, progreso real, cancelación y vencimiento.
- **Ficha de vehículo de video**: Resultado autorizado por fuente/track ID, atributos/placa y referencia de evidencia disponible.
- **Propuesta de inspección temporal**: Flujo futuro de pausa, selección y ficha, con dependencias y criterios de asociación explícitos.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En360/768/1440 y texto200%, el100% de recorridos controlados permite cambiar entre Imagen y Video por teclado/toque, identifica el modo activo y conserva el trabajo vigente sin operaciones extra ni acciones esenciales recortadas.
- **SC-002**: Con configuración válida, ambos modos pueden iniciar sin entrada manual de URL/clave. Una credencial canaria aparece0 veces en artefactos o comunicaciones accesibles al navegador, repositorio e informes; los casos de configuración ausente/inválida, indisponibilidad y rechazo producen estados seguros y no envíos alternativos.
- **SC-003**: En10 escenas controladas, incluidas3 densas, el100% de selecciones y puntos de geometría comprobados conserva identidad y alineación con error de proyección máximo1píxel de pantalla al ajustar,100%,200% y400%; la respuesta visual a zoom/desplazamiento con imagen ya cargada tiene p95<=200ms en el dispositivo documentado y genera0 análisis/enriquecimientos nuevos.
- **SC-004**: En al menos6 clips controlados, incluidos2 densos con21 o más actores y casos de cruces/oclusión/cambio de escena, se conservan clase, geometría y tiempo correctos en todos los cuadros de revisión fijados antes de medir; hay0 etiquetas identificadoras sobre el video y0 asociaciones inventadas con otra trayectoria.
- **SC-005**: En al menos3 tramos continuos controlados con oscilación inicial medible, la oscilación residual de centro/tamaño frente a la trayectoria de referencia disminuye>=20%. En>=95% de cuadros válidos, el contorno presentado mantiene intersección sobre unión>=0.90 con la caja autorizada y desfase<=1cuadro. Si la línea base ya es estable y no existe oscilación medible, se registra esa condición, se conserva su precisión y no se fabrica una ganancia; tampoco se permiten cajas persistentes sin observación válida.
- **SC-006**: Sobre los mismos clips y dispositivo, con modelos, parámetros y carga equivalentes y al menos3 mediciones pareadas, la mediana del tiempo de procesamiento/presentación de video y el pico de memoria de esa etapa no superan110% de la línea base. Se mantienen todos los cuadros y la calidad/duración aprobadas; el coste del enriquecimiento se mide aparte y la interfaz sigue respondiendo en<=1s durante trabajo activo.
- **SC-007**: El100% de escenarios de éxito, espera, preparación final, cero elegibles, fallo parcial, cancelación, interrupción y vencimiento presenta estados y progreso coherentes para ambas etapas. Ninguna etapa activa figura completada y ninguna respuesta tardía restaura evidencia; reproducir un video terminado no espera al enriquecimiento.
- **SC-008**: El100% de vehículos enriquecidos de los clips controlados es accesible con la identidad correcta y resultados legibles, también con paginación; consultar, pausar o buscar en el video genera0 inferencias nuevas. Una lectura ausente/ilegible y una referencia de evidencia antigua se distinguen de una lectura del instante actual.
- **SC-009**: Las regresiones pertinentes de imagen, placas, video, conteo, acceso y limpieza de006/007 pasan, sin cambios de modelos/pesos/umbrales ni cierres ficticios de sus pendientes de aceptación.
- **SC-010**: Al cierre existe una propuesta revisada que cubre pausa/selección/ficha, búsqueda temporal, toque/teclado, estados sin evidencia y asociación por tiempo/track ID; diferencia claramente lo entregado de lo futuro. Los criterios de rendimiento y fluidez se informan como resultados medidos o pendientes, nunca como promesas acreditadas por la especificación.

## Assumptions

- Esta iteración se crea en el checkout principal sobre feature/008-exploracion-imagen-video, conservando los cambios existentes. Cada etapa completada del flujo Spec Kit culminará con un commit de sus archivos pertinentes; no se incluyen credenciales reales, cachés o cambios ajenos ni se publica automáticamente.
- La configuración de entorno sustituye la entrada manual habitual. Una clave privada del backend no se convierte en configuración pública del navegador; la planificación resolverá la entrega segura dentro del despliegue autorizado, manteniendo su protección y acceso vigente. No se incorpora un nuevo sistema de usuarios ni se elimina autenticación.
- El procesamiento es de archivos de video, no de transmisiones en vivo. No se promete procesamiento en tiempo real ni mejora de la exactitud del detector/OCR.
- Se reutilizan seguimiento y enriquecimiento de video existentes. Esta iteración sí cambia presentación/orquestación y puede requerir trabajo en frontend y backend dentro del alcance; la planificación identificará cualquier ampliación contractual necesaria sin alterar silenciosamente contratos previos.
- El enriquecimiento automático comienza cuando el video terminado es elegible; no se exige competir por recursos con su procesamiento. Cambiar de pestaña conserva trabajos admitidos, sin ampliar concurrencia o retención vigentes.
- La fluidez se evalúa contra una línea base tomada antes de modificar la presentación; los umbrales de SC-005/006 son criterios futuros. Las referencias/tramos de evaluación se fijan antes de observar el resultado nuevo; no se ajustan para aparentar mejora.
- La consulta entregada en esta iteración es mediante lista/ficha por track ID junto al reproductor normal. Elegir directamente un contorno del instante pausado será una propuesta para una iteración posterior. Los recortes o medios adicionales solo se mostrarán si existe evidencia autorizada disponible; no se inventan ni se prometen nuevas capturas.
- La propuesta inicial se recoge en [propuesta-inspeccion-video.md](propuesta-inspeccion-video.md) y se revisará al cierre con los contratos/datos realmente disponibles.
- Se mantienen colores sólidos y estilo formal de006/007. Ampliar o estabilizar la representación no modifica los originales ni convierte información interpolada en detalle capturado.
- Los pendientes006/T067–T068 y007/T061–T064/T070 siguen independientes. Esta iteración no acredita mayor exactitud OCR ni los cierra con pruebas sintéticas.
