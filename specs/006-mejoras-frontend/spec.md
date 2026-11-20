# Feature Specification: Exploración visual de imágenes viales enriquecidas

**Feature Branch**: `codex/006-mejoras-frontend`

**Created**: 2026-11-20

**Status**: Draft

**Input**: Mejorar el frontend existente con una apariencia profesional, formal, atractiva y fácil de usar, usando colores sólidos sin gradientes. Analizar y enriquecer imágenes con una sola acción; presentar anotaciones identificadas, recuadros que comuniquen que son pulsables y una ficha por vehículo con atributos, recorte del vehículo y recorte de placa. Trabajar en una rama separada sin interferir con el agente del backend. Diferir el rediseño de video a la siguiente iteración y conservar las funciones actuales.

**Reference**: [005-interfaz-web-prototipo-vial](../005-interfaz-web-prototipo-vial/spec.md).

## Scope Revision — 2026-11-20

El usuario amplía esta iteración para planificar e implementar también los cambios de backend necesarios para el recorrido de imágenes. Se permite continuar en una rama separada en el checkout original cuando se preserve el trabajo existente; el worktree deja de ser obligatorio. Esta autorización sustituye las restricciones anteriores de solo frontend. No autoriza cambiar modelos, pesos, umbrales ni ampliar el rediseño de video.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Analizar y enriquecer una imagen con una sola acción (Priority: P1)

Como usuario autorizado, quiero seleccionar una imagen e iniciar su análisis completo con un único botón, para obtener detecciones y enriquecimiento sin ejecutar pasos técnicos por separado.

**Why this priority**: Elimina la separación manual entre detección y enriquecimiento y ofrece un recorrido claro desde la carga hasta la exploración.

**Independent Test**: Con una imagen válida y el servicio disponible, iniciar una vez el análisis y comprobar que aparecen las detecciones y que el enriquecimiento se inicia automáticamente sobre esa misma imagen.

**Acceptance Scenarios**:

1. **Given** una imagen válida y una sesión autorizada, **When** el usuario pulsa «Analizar imagen», **Then** ve las etapas de análisis y enriquecimiento, y este último comienza automáticamente después de obtener las detecciones, sin un segundo botón.
2. **Given** detecciones disponibles y enriquecimiento todavía activo, **When** el usuario explora el resultado, **Then** puede seleccionar un vehículo y ver sus datos básicos junto con el estado pendiente de sus atributos y placa.
3. **Given** detecciones válidas y un fallo o indisponibilidad del enriquecimiento, **When** termina el intento, **Then** se conserva la imagen anotada, se explica qué parte falta y se permite reintentar solo el enriquecimiento, sin repetir el análisis exitoso.
4. **Given** una imagen sin vehículos elegibles, **When** termina la detección, **Then** se informa de ese resultado, se conservan las demás detecciones y no se inicia un enriquecimiento sin vehículos.
5. **Given** un análisis activo, **When** se pulsa reiteradamente la acción principal o se sustituye la imagen, **Then** no se duplican trabajos por pulsaciones repetidas ni se mezclan resultados de fuentes distintas.

---

### User Story 2 - Seleccionar vehículos directamente sobre la imagen (Priority: P1)

Como usuario, quiero reconocer los recuadros como controles y pulsarlos para inspeccionar un vehículo sin perder el contexto de la escena.

**Why this priority**: Convierte la imagen anotada en la principal herramienta de exploración del resultado.

**Independent Test**: Sobre una escena con varios vehículos, pasar el puntero, seleccionar recuadros, cambiar de vehículo y repetir la operación mediante teclado y toque, comprobando la correspondencia con la ficha.

**Acceptance Scenarios**:

1. **Given** una imagen analizada, **When** el puntero entra en un recuadro vehicular, **Then** el cursor y un cambio visible de borde o énfasis comunican que se puede pulsar, sin ocultar el vehículo.
2. **Given** un recuadro disponible, **When** se activa por clic, toque o teclado, **Then** se resalta como seleccionado y se presenta la ficha del mismo vehículo; la selección se distingue del simple paso del puntero.
3. **Given** varias detecciones, **When** cambia la selección, **Then** el identificador del recuadro, la opción de la lista y la ficha permanecen sincronizados, y solo existe una selección activa.
4. **Given** recuadros superpuestos o muy pequeños, **When** una detección resulta difícil de pulsar, **Then** una lista equivalente permite seleccionar inequívocamente cada vehículo.
5. **Given** una imagen redimensionada, con márgenes o distinta relación de aspecto, **When** se selecciona un vehículo, **Then** la zona activa sigue alineada con su anotación y no incluye márgenes externos a la imagen.
6. **Given** un identificador de seguimiento real disponible, **When** se etiqueta el vehículo, **Then** se muestra como «Track ID»; si no existe, se usa el identificador de detección como «Detección», sin presentarlo como seguimiento real.

---

### User Story 3 - Consultar una ficha enriquecida con evidencia visual (Priority: P1)

Como usuario autorizado, quiero ver los atributos y los recortes del vehículo seleccionado y de su placa, para interpretar el resultado visualmente y conocer la disponibilidad y confianza de cada dato.

**Why this priority**: Hace útil el enriquecimiento y permite revisar la evidencia sin leer respuestas técnicas.

**Independent Test**: Seleccionar varios vehículos con atributos y placas en estados distintos y verificar que la ficha, los recortes y las etiquetas corresponden a la selección correcta.

**Acceptance Scenarios**:

1. **Given** un vehículo seleccionado con enriquecimiento completo, **When** se abre su ficha, **Then** se muestran su identificador, clase, confianza de detección, atributos disponibles con sus confianzas, recorte del vehículo y recorte de placa cuando existe evidencia autorizada suficiente.
2. **Given** una placa localizada pero ilegible, **When** se consulta la ficha, **Then** se puede ver su recorte disponible y la etiqueta «Placa ilegible», sin inventar caracteres.
3. **Given** una placa ausente, una localización fallida o evidencia insuficiente para recortar, **When** se consulta la ficha, **Then** se muestra un estado específico en el lugar del recorte y nunca una imagen de otra detección ni un recorte estimado.
4. **Given** atributos disponibles y lectura de placa fallida, o la situación inversa, **When** se presenta el resultado, **Then** la parte disponible permanece visible y cada sección comunica su estado por separado.
5. **Given** resultados de varios vehículos o de varias páginas, **When** se selecciona cualquiera de ellos, **Then** se asocia con su propio enriquecimiento por identidad, sin depender del orden de llegada o de la posición en una lista.
6. **Given** una ficha abierta, **When** el usuario la cierra, cambia de vehículo o llega nuevo enriquecimiento, **Then** puede continuar explorando sin perder el contexto ni recibir cambios inesperados de selección o foco.

---

### User Story 4 - Usar una interfaz profesional y accesible en distintos dispositivos (Priority: P2)

Como usuario, quiero una interfaz formal y consistente que permita entender qué hacer y leer los resultados cómodamente en móvil, tablet y escritorio.

**Why this priority**: La presentación debe favorecer la interpretación de la evidencia y transmitir calidad sin distraer del análisis.

**Independent Test**: Completar carga, análisis y consulta de una ficha en anchos de 360, 768 y 1440 píxeles, y repetir el recorrido con teclado y ampliación de texto.

**Acceptance Scenarios**:

1. **Given** la pantalla inicial, **When** el usuario la observa, **Then** identifica una acción principal, instrucciones de archivo comprensibles y una jerarquía clara entre carga, progreso y resultados.
2. **Given** cualquiera de los tres tamaños de pantalla, **When** se muestran imagen, lista y ficha, **Then** los controles siguen accesibles, no hay desplazamiento horizontal de toda la página ni texto o acciones recortados, y la imagen conserva su proporción.
3. **Given** la interfaz en cualquier estado, **When** se revisa su apariencia, **Then** usa colores sólidos sin gradientes, tipografía y espaciado consistentes, superficies sobrias y estados de énfasis distinguibles.
4. **Given** una persona que usa teclado o no distingue ciertos colores, **When** recorre la interfaz, **Then** puede identificar el foco, activar controles y entender estados mediante texto o indicadores adicionales al color.
5. **Given** un archivo rechazado, un fallo o una sesión vencida, **When** aparece el mensaje, **Then** explica la situación con lenguaje comprensible e indica la siguiente acción posible sin exponer detalles internos.

---

### User Story 5 - Conservar las capacidades existentes y la privacidad de sesión (Priority: P2)

Como usuario del prototipo, quiero conservar las funciones de imagen, video y conteo ya disponibles y controlar los datos temporales de mi sesión.

**Why this priority**: La mejora de imágenes debe integrarse sin romper otros recorridos ni ampliar la conservación de datos sensibles.

**Independent Test**: Completar los recorridos existentes de video y conteo con evidencia controlada, y reiniciar una sesión con imagen enriquecida y trabajos activos.

**Acceptance Scenarios**:

1. **Given** los flujos actuales de video, conteo y enriquecimiento de video, **When** se usan tras esta iteración, **Then** mantienen las capacidades acordadas en 005 sin incorporar la nueva exploración interactiva de video.
2. **Given** resultados, recortes o una placa legible visibles, **When** el usuario reinicia la demostración, cambia la identidad de acceso o cierra la sesión de navegación, **Then** dejan de estar accesibles en la interfaz y no quedan guardados como historial.
3. **Given** trabajos activos al reiniciar, **When** se solicita el reinicio, **Then** se intenta su cancelación y se limpia inmediatamente la sesión visible aunque no pueda confirmarse la cancelación.
4. **Given** una fuente vencida o acceso rechazado, **When** se intenta abrir su evidencia, **Then** se retiran los datos afectados y se indica cómo comenzar un nuevo análisis autorizado.

---

### Edge Cases

- Cero detecciones, detecciones de actores no vehiculares o vehículos sin enriquecimiento elegible.
- Archivo inválido, demasiado grande, no decodificable o sustituido mientras hay solicitudes pendientes.
- Error de detección frente a error de enriquecimiento: cada uno conserva o elimina solo los resultados que corresponden.
- Respuestas tardías de una imagen anterior, pulsaciones repetidas, reintentos y cambios de credencial o servicio durante una operación.
- Detecciones solapadas, cajas diminutas, etiquetas que se superponen, orientación o proporción de imagen diferente y redimensionamiento con ficha abierta.
- Datos de enriquecimiento paginados, resultados desordenados, incompletos o con identificadores sin correspondencia: no se asignan por similitud ni posición.
- Falta de identificador de seguimiento real en una imagen estática.
- Placa legible, ilegible, ausente o fallida; atributos fallidos con placa disponible, y viceversa.
- Coordenadas inválidas, evidencia no autorizada o imagen original no disponible para un recorte fiel: mostrar indisponibilidad sin aproximar.
- Vencimiento, cancelación, pérdida de conexión o falta de modelos durante la consulta y mientras una ficha está abierta.
- Navegación por teclado, dispositivo sin puntero, texto ampliado al 200% y movimiento reducido.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: La interfaz MUST conservar las capacidades vigentes de 005 y concentrar esta iteración en el recorrido de imágenes; el rediseño funcional y visual específico de video queda para la siguiente iteración.
- **FR-002**: La interfaz MUST permitir seleccionar, previsualizar y sustituir una imagen válida, informar los límites aplicables y ofrecer una única acción principal para iniciar análisis y enriquecimiento.
- **FR-003**: Tras un análisis de imagen exitoso con vehículos elegibles, la interfaz MUST iniciar automáticamente el enriquecimiento de esa misma fuente vigente, sin una segunda acción manual.
- **FR-004**: La interfaz MUST diferenciar visualmente las etapas de detección y enriquecimiento y los estados de espera, procesamiento, éxito, resultado parcial, vacío, fallo, cancelación y vencimiento; no mostrará porcentajes no respaldados por información real.
- **FR-005**: Las detecciones y la imagen anotada MUST poder consultarse mientras llega el enriquecimiento; un fallo de este último no eliminará el análisis ya obtenido. Un reintento de enriquecimiento no repetirá una detección exitosa.
- **FR-006**: La interfaz MUST impedir duplicaciones por pulsaciones reiteradas y evitar mezclar respuestas de fuentes, credenciales o sesiones anteriores con la fuente activa.
- **FR-007**: Cada vehículo detectado MUST disponer de un recuadro seleccionable, alineado con la imagen presentada, y una etiqueta legible con su identificador y clase. Las detecciones no vehiculares existentes se conservarán sin aparentar disponer de enriquecimiento vehicular.
- **FR-008**: Los recuadros MUST comunicar su carácter pulsable mediante cursor y énfasis al pasar el puntero, y distinguir claramente foco y selección sin depender únicamente del color ni tapar la evidencia.
- **FR-009**: La selección MUST funcionar por clic, toque y teclado; una lista equivalente de vehículos permitirá acceder a detecciones pequeñas, superpuestas o difíciles de pulsar. La lista y la ficha compartirán una única selección activa.
- **FR-010**: Al redimensionar la imagen, cambiar la orientación o distribuir de nuevo los paneles, las zonas activas MUST conservar su correspondencia con las anotaciones y respetar la proporción y los márgenes de la imagen.
- **FR-011**: La ficha MUST mostrar el identificador real disponible, clase, confianza de detección, atributos enriquecidos con sus confianzas y estados independientes de atributos y placa, con nombres comprensibles y sin respuestas técnicas crudas.
- **FR-012**: La interfaz MUST mostrar «Track ID» únicamente para un identificador de seguimiento real entregado por el servicio. Si falta, mostrará «Detección» y explicará que el seguimiento no está disponible; nunca renombrará una detección como seguimiento. La entrega de Track ID real en imágenes queda registrada como dependencia externa pendiente, no como capacidad satisfecha por este reemplazo.
- **FR-013**: La ficha MUST incluir un recorte fiel del vehículo y otro de la placa cuando exista evidencia autorizada y suficiente para delimitarlos inequívocamente. Los recortes deberán corresponder al mismo vehículo y proceder de la imagen original disponible, sin añadir, reconstruir o mejorar artificialmente detalles.
- **FR-014**: La ficha MUST distinguir placa legible, ilegible, no detectada, fallida y recorte no disponible. Solo mostrará texto completo de placa autorizado y marcado como legible; no deducirá caracteres ni ocultará un recorte localizado solo porque la lectura sea ilegible.
- **FR-015**: La correspondencia entre recuadro, ficha, recortes y enriquecimiento MUST mantenerse por la identidad de la detección de origen, incluso con resultados desordenados o paginados. Un resultado sin correspondencia no se mostrará en otro vehículo.
- **FR-016**: Cambiar o cerrar una ficha MUST conservar el contexto de la imagen y permitir continuar explorando; las actualizaciones de enriquecimiento no modificarán por sí solas la selección ni robarán el foco. Si se usa una presentación superpuesta, será cerrable por teclado y devolverá el foco al control que la abrió.
- **FR-017**: Toda la interfaz afectada MUST mantener una apariencia formal y profesional, colores sólidos sin gradientes, tipografía y espaciado consistentes, contraste suficiente y jerarquía explícita entre acción principal, información secundaria y estados.
- **FR-018**: La carga, imagen, lista y ficha MUST ser utilizables a anchos de 360, 768 y 1440 píxeles sin desplazamiento horizontal de la página, acciones inaccesibles ni texto truncado esencial. El detalle podrá redistribuirse sin perder la selección.
- **FR-019**: Los controles MUST tener nombres accesibles, foco visible y orden lógico; los estados relevantes se comunicarán sin exigir visión del color. El texto normal tendrá contraste mínimo 4.5:1, los indicadores de foco y controles 3:1, y los objetivos táctiles principales un área mínima de 44 por 44 píxeles. Para cajas pequeñas se dispondrá del control equivalente en la lista.
- **FR-020**: La interfaz MUST seguir siendo operable con texto ampliado al 200% y no requerir animaciones para interpretar estados; respetará la preferencia de movimiento reducido.
- **FR-021**: Los mensajes de validación, autorización, indisponibilidad y vencimiento MUST ser comprensibles, conservar el contexto útil y ofrecer una acción de recuperación cuando exista, sin mostrar secretos, rutas internas ni contenido sensible en errores.
- **FR-022**: La credencial, dirección del servicio, archivos, identificadores, resultados y recortes MUST mantenerse exclusivamente durante la sesión activa según las reglas de 005; no se añadirá historial, exportación, persistencia de placas ni registro de sus imágenes o texto.
- **FR-023**: Reiniciar, sustituir la identidad de acceso o cerrar la sesión MUST retirar la evidencia y los datos sensibles afectados. El reinicio intentará cancelar los trabajos activos y limpiará la vista incluso si la cancelación falla. Una respuesta tardía no podrá restaurar una sesión eliminada.
- **FR-024**: La interfaz MUST respetar la autorización y el vencimiento de la evidencia; ante rechazo o expiración retirará los datos afectados y solicitará un nuevo análisis o acceso válido, sin inventar vigencias ni mecanismos de autenticación nuevos.
- **FR-025**: Esta iteración MUST abarcar el frontend y las correcciones de backend y contratos necesarias para completar y proteger el recorrido de imágenes. Los cambios conservarán compatibilidad con clientes existentes y no sustituirán autenticación, modelos, pesos o umbrales aprobados. Las especificaciones históricas conservarán su significado; los contratos nuevos se documentarán en 006.
- **FR-026**: La información no disponible MUST identificarse explícitamente. Las carencias de servicio abordadas por este plan se convertirán en trabajo implementable dentro de 006; solo quedarán como dependencias externas los recursos o capacidades realmente fuera de alcance. No se declarará una capacidad completada mediante datos inventados.
- **FR-027**: El trabajo MUST permanecer en `codex/006-mejoras-frontend`. Puede utilizar el checkout original al dejar de existir trabajo paralelo de backend, preservando cambios y archivos ajenos y sin alterar la rama histórica del backend. El worktree separado deja de ser obligatorio.
- **FR-028**: El sistema MUST utilizar una única orientación, dimensiones y geometría válidas para la imagen analizada, sus anotaciones, sus detecciones y sus recortes. Las cajas inválidas no producirán evidencia aproximada ni identidades inconsistentes.
- **FR-029**: El sistema MUST informar qué detecciones admiten enriquecimiento y hasta cuándo están disponibles la fuente y su evidencia, sin exigir que el usuario conozca reglas internas de elegibilidad o conservación.
- **FR-030**: El servicio MUST informar la disponibilidad real de atributos, localización de placa y lectura, distinguiendo capacidades ausentes. La indisponibilidad de una rama no bloqueará las detecciones ni los resultados válidos de otra.
- **FR-031**: El sistema MUST impedir la publicación de resultados posteriores a cancelación o vencimiento y conservar las transiciones terminales frente a respuestas tardías o operaciones concurrentes. El procesamiento cooperativo se detendrá entre unidades, sin prometer interrumpir una inferencia ya iniciada.
- **FR-032**: El servicio MUST eliminar la evidencia temporal y los resultados sensibles al vencer su vigencia sin depender de una nueva solicitud del usuario; la limpieza periódica tendrá un margen máximo de 2 segundos y un cierre ordenado.
- **FR-033**: El servicio MUST suprimir el texto de placa no autorizado o no legible antes de guardar o responder cualquier representación de resultados, manteniendo el recorte localizado cuando sea válido.

### Key Entities

- **Sesión de exploración**: Acceso temporal, servicio seleccionado, imagen activa, operaciones en curso y datos visibles; se descarta al reiniciar o cerrar la navegación.
- **Fuente de imagen**: Archivo original seleccionado, dimensiones, referencia de análisis y vigencia; todos sus resultados pertenecen a la misma fuente.
- **Detección seleccionable**: Actor detectado con identificador, clase, confianza y recuadro; los vehículos elegibles ofrecen ficha enriquecida.
- **Identificador de seguimiento**: Referencia temporal real entregada por el servicio cuando existe, distinta del identificador de una detección estática y de una identidad real del vehículo.
- **Proceso de enriquecimiento**: Operación asociada a una fuente analizada, con estado, resultados parciales o completos, errores y vencimiento.
- **Ficha del vehículo**: Selección activa que reúne detección, atributos, confidencias, evidencia del vehículo y estado de placa, sin mezclar fuentes.
- **Evidencia recortada**: Vista temporal fiel de una región autorizada de la imagen original, vehicular o de placa, con disponibilidad y vínculo inequívoco con la detección.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En el 100% de los casos controlados con imagen válida y vehículos elegibles, una sola activación de «Analizar imagen» inicia detección y después enriquecimiento sin una segunda acción; pulsaciones repetidas no duplican operaciones.
- **SC-002**: En un conjunto controlado de al menos 10 imágenes y 20 vehículos, el 100% de las selecciones relaciona el recuadro y la ficha con el vehículo correcto, incluidos resultados desordenados o paginados y cajas superpuestas.
- **SC-003**: Con resultados ya disponibles y sin esperar procesamiento adicional, la ficha del vehículo seleccionado aparece en menos de 1 segundo en el dispositivo de evaluación documentado.
- **SC-004**: El 100% de los recortes presentados en el conjunto controlado corresponde al vehículo o placa seleccionados; cuando falta evidencia suficiente, el 100% de esos casos muestra indisponibilidad explícita en lugar de una imagen aproximada o ajena.
- **SC-005**: El recorrido completo de carga, selección y consulta puede realizarse por teclado y por toque; en 360, 768 y 1440 píxeles y con texto ampliado al 200% no hay acciones esenciales inaccesibles ni desplazamiento horizontal de toda la página.
- **SC-006**: Todas las pantallas y estados afectados cumplen el uso de colores sólidos sin gradientes y los mínimos de contraste y acceso de FR-019, verificados con una revisión visual y de accesibilidad registrada.
- **SC-007**: Al menos 4 de 5 personas representativas, sin conocer el funcionamiento técnico, pueden iniciar un análisis y localizar la ficha de un vehículo sin ayuda, en un máximo de 2 minutos de interacción activa, excluyendo espera de procesamiento; al menos 4 de 5 califican claridad y presentación con 4 o más sobre 5.
- **SC-008**: El 100% de los casos controlados de enriquecimiento fallido conserva las detecciones válidas; el 100% de errores, cancelaciones, resultados vacíos y vencimientos probados termina en un estado comprensible sin dejar una espera indefinida.
- **SC-009**: Tras reiniciar o cambiar la identidad de acceso, el 100% de resultados y recortes anteriores desaparece y ninguna respuesta tardía vuelve a mostrarlos; no se conserva texto de placa ni credenciales fuera de la sesión.
- **SC-010**: Los recorridos de video y conteo definidos en 005 siguen superando sus comprobaciones pertinentes de regresión con evidencia controlada, sin exigir el rediseño de video diferido.
- **SC-011**: El 100% de etiquetas «Track ID» visibles corresponde a seguimiento real recibido; los casos sin ese dato usan una etiqueta de detección. El objetivo de Track ID real para imágenes se considera pendiente mientras la dependencia externa DEP-001 no esté disponible.
- **SC-012**: En imágenes controladas con orientación normal, rotada y reflejada, el 100% de cajas y recortes coincide con la evidencia del mismo vehículo y de la misma placa, incluyendo cajas en los bordes.
- **SC-013**: El 100% de pruebas de cancelación o vencimiento concurrentes con finalización impide publicar resultados posteriores; la evidencia y los resultados sensibles vencidos se eliminan en un máximo de 2 segundos incluso sin solicitudes nuevas.
- **SC-014**: En los casos de modelos ausentes, disponibles por separado o completos, la disponibilidad informada coincide con la real; ninguna representación persistida o entregada contiene texto de placa cuando su estado no es legible.

## Assumptions

- El objetivo es elevar la calidad de la interfaz existente; no implica certificar producción, cambiar el modelo ni alterar el significado de sus predicciones.
- «De una al analizar» significa una única acción de usuario que encadena análisis y enriquecimiento sobre la misma fuente; no exige crear una operación nueva en el backend.
- El recorrido enriquecido nuevo se limita a imágenes. Video y conteo conservarán su funcionamiento; podrán heredar estilos comunes siempre que no se emprenda su rediseño ni se introduzcan regresiones.
- Se prefiere que la ficha acompañe a la imagen en pantallas amplias y se redistribuya en pantallas pequeñas; el detalle de composición se decidirá en el plan manteniendo los criterios de acceso y contexto.
- El identificador de detección es la referencia provisional explícita para imágenes que no disponen de seguimiento real. No satisface ni simula la dependencia de Track ID solicitada.
- El archivo original puede conservarse temporalmente durante la sesión para presentar recortes fieles autorizados; los recortes no añaden almacenamiento ni historial. La evidencia disponible debe permitir asociar y delimitar cada región sin suposiciones.
- Se mantienen las reglas de autorización, vigencia, cancelación y visualización local de placas definidas en 005 y la constitución del proyecto.
- La base inspeccionada es `81bc12d`, con el frontend de 005. Se permite incorporar explícitamente el trabajo ya confirmado del backend antes de continuar en la rama 006; los archivos sin confirmar no se incorporarán ni sobrescribirán por conveniencia.
- El conjunto de evaluación utilizará imágenes y videos controlados y autorizados; se documentarán dispositivo y condiciones para cualquier medición de tiempo. Esta especificación fija criterios futuros y no afirma que ya se hayan medido.

## Dependencies & Scope Boundaries

- **DEP-001 — Track ID real para imágenes**: El comportamiento actual ofrece identificación de detección en imágenes y reserva el seguimiento para video. Si se requiere «Track ID» también en imágenes, su disponibilidad y significado deben acordarse y entregarse externamente. Hasta entonces se aplica FR-012 y se mantiene esta capacidad pendiente.
- **DEP-002 — Evidencia para recortes**: Se resolverá dentro de 006 mediante imagen canónica protegida, geometría coherente y vigencia explícita. Si falta localización fiable de una placa, su recorte seguirá figurando como no disponible.
- **DEP-003 — Enriquecimiento operativo y asociación estable**: 006 incluirá correcciones de disponibilidad, asociación, saneamiento y ciclo de vida. Los pesos, manifiestos y recursos privados válidos siguen siendo prerrequisitos del entorno, sin sustituirlos ni fabricarlos.
- **DEP-004 — Acceso autorizado al servicio y artefactos**: 006 mantendrá la autenticación existente y aplicará los mismos permisos a la evidencia añadida. Se permiten ajustes de compatibilidad necesarios sin abrir acceso público ni ampliar la retención.
- Los hallazgos y trabajos de backend incluidos se registran en [dependencias-backend.md](dependencias-backend.md), con contratos y fases de implementación en el plan de 006.
- No se incluyen exploración por recuadros en video, rediseño del reproductor, nuevos algoritmos de seguimiento, detección, OCR o enriquecimiento, historial persistente, exportación de placas, nuevas cuentas ni despliegue.
