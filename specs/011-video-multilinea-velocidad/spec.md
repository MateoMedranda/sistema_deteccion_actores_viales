# Feature Specification: Velocidad de reproducción y múltiples líneas de conteo

**Feature Branch**: `feature/011-video-multilinea-velocidad`

**Created**: 2026-11-25

**Status**: Especificada — lista para planificación; funcionalidad pendiente de implementación.

**Input**: User description: "Crear una nueva iteración para controlar la velocidad del video e implementar más de una línea de conteo en intersecciones. Sacar el contador a una barra superior con varios contadores. Dar nombre a cada línea, por ejemplo AV SIMÓN BOLIVAR y RUTA VIVA, permitir cambiar su color desde el contador y mostrar nombre y color en su tarjeta. Usar otra rama."

**Requisito previo vigente**: El usuario retiró la necesidad de elegir sentido: contar cruces en cualquiera de los dos sentidos, sin flecha ni «Invertir sentido». Esa solicitud quedó interrumpida antes de modificar código y se integra en esta iteración.

**Referencias**: [009-video-progresivo](../009-video-progresivo/spec.md), [010-video-detalle-conteo](../010-video-detalle-conteo/spec.md) y su [corrección de catálogo multiclase](../010-video-detalle-conteo/class-count-fix.md). Las decisiones de 010 sobre un único sentido con flecha son antecedentes sustituidos por los requisitos de 011; las demás capacidades existentes se conservan.

**Alcance de esta etapa**: Especificación, checklist de calidad, registro documental/metodológico y commit en el checkout principal. La implementación posterior comprenderá interfaz y servicios necesarios. No se cambia código de producto en esta etapa.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Configurar varias líneas con nombre (Priority: P1)

Como analista de una intersección, quiero dibujar una línea por acceso y nombrarla para distinguir las vías que estoy observando.

**Why this priority**: Un único segmento no permite distinguir cruces en accesos diferentes.

**Independent Test**: Antes de iniciar un video, crear AV SIMÓN BOLIVAR y RUTA VIVA sobre el primer fotograma, ajustar cada segmento y comprobar que ambas configuraciones se conservan al iniciar el análisis.

**Acceptance Scenarios**:

1. **Given** un video seleccionado, **When** añado dos líneas y asigno esos nombres, **Then** ambas aparecen sobre el primer fotograma y cada una tiene una identidad y una tarjeta propias.
2. **Given** varias líneas, **When** selecciono una y arrastro sus extremos o el segmento completo, **Then** solo cambia esa línea y el movimiento conserva la suavidad del editor existente.
3. **Given** una configuración válida, **When** añado, modifico o elimino otra línea durante el análisis o al finalizar, **Then** las demás líneas conservan su geometría y sus conteos.
4. **Given** un borrador incompleto o un nombre inválido, **When** intento aplicarlo, **Then** se explica el problema y la configuración confirmada sigue vigente.

---

### User Story 2 - Contar cada cruce en ambos sentidos (Priority: P1)

Como analista, quiero que cada línea cuente a los vehículos que realmente la atraviesan, sin configurar sentidos ni interpretar flechas.

**Why this priority**: El total por vía es el objetivo; la dirección seleccionable añade una restricción que el usuario ha retirado.

**Independent Test**: Usar trayectorias controladas que crucen dos segmentos desde lados opuestos, incluyan repeticiones y contactos, y contrastar cada total con los cruces reales de ese segmento.

**Acceptance Scenarios**:

1. **Given** vehículos conocidos que cruzan una línea desde lados opuestos, **When** se confirman sus trayectorias, **Then** ambos suman al mismo contador sin flechas ni selector de sentido.
2. **Given** un vehículo que cruza dos líneas, **When** se confirman ambos pasos, **Then** suma una vez en cada línea; volver a atravesar una de ellas no lo cuenta otra vez en esa línea.
3. **Given** un vehículo que solo toca el segmento o atraviesa su prolongación, **When** continúa su trayectoria sin cruzar el segmento real, **Then** no aumenta ese contador.
4. **Given** conteos calculados, **When** retrocedo y vuelvo al mismo instante, **Then** veo los mismos totales históricos por línea sin duplicaciones ni resultados del futuro.
5. **Given** un segmento nuevo o desplazado sobre un tramo ya analizado, **When** lo aplico, **Then** su contador se recalcula sobre las observaciones disponibles sin repetir el análisis de vehículos; mientras tanto se muestra que está calculándose.

---

### User Story 3 - Consultar y personalizar los contadores superiores (Priority: P1)

Como analista, quiero una barra por encima del video con una tarjeta por línea, que muestre su nombre, color y cantidad, y permita cambiar su color desde esa misma tarjeta.

**Why this priority**: La asociación visible entre vía, segmento y cantidad evita confundir resultados en una intersección.

**Independent Test**: Crear tres líneas, cambiar el color desde una tarjeta y verificar la correspondencia con su segmento, sin que cambien cantidades ni las otras líneas.

**Acceptance Scenarios**:

1. **Given** varias líneas confirmadas, **When** consulto el video, **Then** la barra superior muestra una tarjeta por línea con nombre, color y total del instante reproducido, fuera de la imagen.
2. **Given** una tarjeta, **When** cambio su color a otro válido, **Then** tarjeta y segmento reflejan el mismo color; las cantidades, geometrías y demás colores no cambian.
3. **Given** varias líneas cercanas o que se cruzan, **When** selecciono una tarjeta o línea, **Then** se resalta la asociación correspondiente sin depender únicamente del color.
4. **Given** nombres largos o diez tarjetas en una pantalla pequeña, **When** navego por ellas, **Then** puedo identificar y editar cada línea sin desbordamiento horizontal de la página ni ocultar los controles principales.

---

### User Story 4 - Elegir la velocidad de reproducción (Priority: P2)

Como analista, quiero ralentizar el video para inspeccionar un cruce o acelerarlo para revisar un tramo ya analizado, manteniendo sincronizadas las cajas y las cantidades.

**Why this priority**: Permite alternar revisión detallada y exploración rápida sin cambiar el procesamiento ni la validez del conteo.

**Independent Test**: En un tramo completamente analizado, reproducir una duración conocida a 0,5×/1×/2×; comprobar tiempo transcurrido, sincronización y totales al llegar al mismo instante.

**Acceptance Scenarios**:

1. **Given** un video reproducible, **When** elijo 0,5× o 2×, **Then** la reproducción cambia de ritmo desde su posición actual y el control muestra la velocidad seleccionada.
2. **Given** el video pausado, **When** cambio la velocidad, **Then** permanece pausado en el mismo instante y emplea esa velocidad cuando lo reanudo.
3. **Given** reproducción acelerada que alcanza el límite analizado, **When** no hay más tramo confirmado, **Then** se detiene la progresión, se explica la espera y solo se reanuda cuando hay datos disponibles, conservando la velocidad elegida.
4. **Given** la misma trayectoria vista a distintas velocidades, **When** llego al mismo instante, **Then** las cajas, inspección y contadores corresponden a ese instante y los totales son iguales.

---

### User Story 5 - Conservar el contexto al retomar el video (Priority: P2)

Como analista, quiero recuperar las líneas y sus resultados al retomar un trabajo vigente, sin mezclar configuraciones de otros videos ni confundir resultados pendientes con ceros.

**Why this priority**: La revisión puede interrumpirse mientras el análisis sigue avanzando y debe conservar sus referencias.

**Independent Test**: Reabrir un trabajo vigente con varias líneas, nombres y colores; verificar cantidades por instante, y luego cambiar a otro video o dejar vencer el primero.

**Acceptance Scenarios**:

1. **Given** un trabajo vigente con líneas guardadas, **When** recargo o recupero la conexión, **Then** se restauran líneas, nombres, colores y conteos confirmados, sin duplicar líneas ni ampliar la disponibilidad del resultado.
2. **Given** un trabajo anterior con una sola línea en un sentido, **When** se adapta a esta experiencia, **Then** conserva su segmento, recibe un nombre/color editables y se recalcula en ambos sentidos si conserva las observaciones necesarias; no se presenta el total antiguo como si ya incluyera ambos sentidos.
3. **Given** datos insuficientes, procesamiento parcial o resultado vencido, **When** consulto una tarjeta, **Then** distingue calculando, parcial o no disponible de un cero confirmado y explica si hace falta analizar de nuevo.
4. **Given** otro video o sesión, **When** cambio de contexto, **Then** no se aplican líneas, cantidades ni preferencias temporales del video anterior.

### Edge Cases

- Segmento incompleto, extremos iguales o fuera de la escena; cancelar el borrador no elimina una línea confirmada.
- Nombres vacíos, repetidos con diferencias solo de espacios/mayúsculas o que contienen acentos; nombres largos siguen siendo consultables completos.
- Dos líneas superpuestas o que se intersectan: seleccionar una no arrastra ni elimina otra; cada identidad puede sumar en ambas si realmente cruza ambas.
- Dos vehículos que cruzan simultáneamente, varias clases en el mismo cuadro y clases cuya etiqueta cambia posteriormente; no usar el número máximo de identidad como cantidad.
- Roce, trayectoria tangente, centro sobre la línea durante varias mediciones, vehículo presente inicialmente sobre la línea y vibración de cajas; solo una transición de lado confirmada cuenta.
- Cuadros de posición estimada entre detecciones no confirman cruces por sí solos; se mantiene la limitación del seguimiento ante pérdidas/reasignaciones de identidad.
- Renombrar/recolorear repetidamente durante reproducción, recalcular varias líneas a la vez o recibir una respuesta tardía para una línea editada/eliminada.
- Cambio de velocidad repetido, pausa, cambio de pestaña o pantalla completa; ninguna acción concede acceso al tramo no analizado ni inicia enriquecimiento automáticamente.
- Alcanzar el límite de análisis a 2× y luego retroceder; se puede volver al tramo disponible sin perder la velocidad elegida.
- Se alcanza la capacidad admitida de líneas: informar el límite y conservar todas las ya confirmadas.
- Vencimiento, retirada del trabajo o pérdida de conexión durante una modificación; no publicar cantidades de otra revisión ni conservar medios por más tiempo.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE permitir crear y gestionar varias líneas independientes para un mismo video, con capacidad verificable de al menos 10 líneas simultáneas; cualquier límite operativo DEBE comunicarse antes de rechazar otra línea sin alterar las existentes.
- **FR-002**: Cada línea DEBE tener identidad estable, nombre, color sólido, segmento, estado de cálculo y conteo propios; no se DEBEN identificar líneas por su posición en una lista ni por su color.
- **FR-003**: El usuario DEBE poder crear líneas sobre el primer fotograma antes de iniciar el análisis y gestionarlas durante el procesamiento o al finalizar, usando el editor de referencia sin tener que volver a cargar el video.
- **FR-004**: El editor DEBE permitir seleccionar una línea, dibujarla, arrastrar cualquiera de sus extremos o desplazar el segmento completo con suavidad mediante ratón/tacto, y ajustar sus puntos mediante teclado. Editar una no DEBE mover las demás.
- **FR-005**: Los nombres DEBEN admitir entre 1 y 60 caracteres visibles tras limpiar espacios exteriores; DEBEN conservar acentos y texto del usuario. Nombres vacíos o duplicados ignorando mayúsculas y espacios redundantes DEBEN rechazarse con una explicación. Se DEBE proponer un nombre inicial único como «Línea 1».
- **FR-006**: Cada línea nueva DEBE recibir un color distinto de las demás líneas activas. Desde su tarjeta, el usuario DEBE poder cambiarlo por otro color sólido disponible; un color idéntico al de otra línea DEBE señalarse antes de confirmar, conservando el anterior.
- **FR-007**: El cambio confirmado de nombre o color DEBE reflejarse conjuntamente en tarjeta, editor y línea del reproductor; no DEBE reiniciar conteos, modificar geometrías ni ejecutar de nuevo el análisis.
- **FR-008**: El sistema DEBE mostrar una barra inmediatamente por encima del reproductor con una tarjeta por línea que incluya nombre, color y cantidad del instante reproducido, o su estado de cálculo. Esta barra sustituye al contador único dentro de la imagen.
- **FR-009**: Seleccionar una tarjeta o segmento DEBE identificar la misma línea en ambos lugares mediante foco/resaltado y nombre accesible. El color no DEBE ser la única forma de asociación.
- **FR-010**: Cada línea DEBE contar cruces reales en cualquiera de los dos sentidos con un único total. La experiencia nueva no DEBE mostrar flechas de sentido, «Invertir sentido» ni controles que restrinjan el lado desde el que se cuenta.
- **FR-011**: Un cruce válido DEBE confirmarse con mediciones reales sucesivas de la misma identidad cuyo centro pasa de un lado al otro e intersecta el segmento finito. El contacto sin transición, la prolongación y las posiciones únicamente estimadas no DEBEN sumar; una referencia inicial sobre la línea no demuestra cruce.
- **FR-012**: Para una misma geometría confirmada, cada identidad vehicular DEBE sumar como máximo una vez por línea, aunque vuelva a cruzarla o se repita la reproducción. Un vehículo que atraviesa varias líneas DEBE poder sumar una vez en cada una. Las tarjetas no representan conjuntos mutuamente excluyentes y no DEBEN sumarse como total de vehículos únicos del video.
- **FR-013**: El conteo DEBE reconocer las seis clases actuales del modelo, incluidas camión pesado, camión y furgoneta, usando el catálogo aprobado; personas y clases no catalogadas no suman cruces. Cambios posteriores de etiqueta o enriquecimiento no DEBEN reescribir la clase del cruce confirmado. El resumen global de detecciones mantiene su política independiente.
- **FR-014**: Crear o cambiar la geometría de una línea DEBE recalcular únicamente sus cruces sobre el tramo ya analizado y continuar con los nuevos; no DEBE repetir la detección ni borrar los resultados de otras líneas. La nueva revisión DEBE distinguir resultados pendientes de cero y descartar respuestas de la revisión anterior.
- **FR-015**: Renombrar/recolorear no cambia el significado de los cruces; cambiar geometría inicia una nueva revisión de esa línea. Cancelar un borrador DEBE mantener la configuración confirmada; eliminar explícitamente una línea DEBE retirar solo su segmento, tarjeta y resultados asociados.
- **FR-016**: Cada tarjeta DEBE mostrar el total acumulado hasta la posición del cuadro que se está viendo, limitado a la cobertura confirmada de su línea. Retroceder y volver al mismo instante DEBE dar el mismo total; cobertura pendiente, resultado parcial, no disponible y cero confirmado DEBEN distinguirse.
- **FR-017**: El usuario DEBE disponer de velocidades 0,25×,0,5×,0,75×,1×,1,25×,1,5× y 2×, con 1× inicial y selección visible/accesible junto a los controles de reproducción. Un video nuevo DEBE empezar a 1×; cambiar de pestaña dentro del mismo trabajo mantiene la selección.
- **FR-018**: Cambiar velocidad DEBE conservar el instante actual y el estado de pausa/reproducción. Cajas, tiempos, selección de vehículos y cantidades DEBEN seguir el tiempo de la fuente, sin adelantarse ni retrasarse por usar otra velocidad.
- **FR-019**: La velocidad DEBE afectar solo a la reproducción: no cambia detección, seguimiento, cadencia de análisis, enriquecimiento ni cantidades calculadas. No se DEBE prometer que acelerar la reproducción acelera el análisis.
- **FR-020**: Se DEBE mantener el bloqueo de avance más allá del prefijo analizado, tanto por reproducción como búsqueda. Al alcanzar ese límite DEBE indicarse la espera; la intención de reproducción previa se puede reanudar al haber datos, pero una pausa explícita DEBE respetarse. Se conserva la velocidad elegida.
- **FR-021**: Las líneas confirmadas, sus nombres/colores y resultados DEBEN recuperarse al reabrir el mismo trabajo mientras siga vigente. Configuraciones, borradores y respuestas de otro video/sesión no DEBEN mezclarse.
- **FR-022**: La transición desde un trabajo vigente de una sola línea DEBE conservar su geometría y ofrecerla como una línea editable; si era direccional, su total DEBE recalcularse para ambos sentidos antes de mostrarse como nuevo conteo. Si faltan observaciones suficientes, se DEBE declarar no disponible o requerir nuevo análisis; no inventar cruces ni confundir el total antiguo con el nuevo.
- **FR-023**: Barra de tarjetas, editor y control de velocidad DEBEN ser utilizables a 360,768 y 1440 píxeles de ancho, con ratón, tacto y teclado, nombres accesibles, foco visible y contraste de texto/controles. No DEBE haber desbordamiento horizontal de la página. En pantalla completa, los contadores y controles DEBEN seguir accesibles sin tapar los vehículos de la escena.
- **FR-024**: Se DEBEN conservar autorización, privacidad y vencimiento vigentes de los trabajos. Reabrir, editar, cambiar velocidad o recalcular líneas no DEBE extender la conservación ni publicar fuentes, recortes o resultados a usuarios distintos del autorizado.
- **FR-025**: Se DEBEN conservar la sección de imágenes, enriquecimiento selectivo por instante, presentación multiclase, resumen global y exportación explícita existentes. Velocidad seleccionada y tarjetas multicontador no alteran por sí mismas el tiempo ni el contenido de las exportaciones existentes.
- **FR-026**: Un error de edición/cálculo DEBE conservar la última configuración confirmada, identificar la línea afectada y permitir recuperación sin duplicar líneas, cruces ni análisis. Una respuesta tardía de una línea eliminada no DEBE recrearla.

### Key Entities *(include if feature involves data)*

- **Trabajo de video**: Contexto temporal autorizado de la fuente, reproducción, observaciones y colección de líneas; posee un plazo de disponibilidad que estas mejoras no amplían.
- **Línea de conteo**: Identidad estable dentro del trabajo, nombre, color, dos extremos y revisión geométrica. Nombre y color describen la misma línea sin cambiar la historia de cruces.
- **Borrador de línea**: Cambios todavía no aplicados; no sustituyen la última geometría confirmada ni sus cantidades.
- **Cruce confirmado por línea**: Identidad vehicular, línea/revisión, instante de confirmación y clase observada. Su unicidad es por identidad y línea/revisión, no global entre accesos.
- **Tarjeta de contador**: Nombre, color, selección, cantidad histórica y estado/cobertura correspondientes a una línea; forma parte de la barra superior.
- **Preferencia de reproducción**: Velocidad elegida y estado pausado/reproduciendo del video actual; independiente del progreso de análisis y del tiempo de la fuente.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En un video controlado se configuran y recuperan al menos 10 líneas con nombres y colores distintos; crear, mover, renombrar o borrar una no altera la geometría ni los resultados confirmados de las otras.
- **SC-002**: En trayectorias controladas con las seis clases actuales y cruces desde ambos lados, cada tarjeta coincide exactamente con el conteo manual de su segmento; cero duplicados por identidad/línea y cero aumentos por contactos, prolongaciones o cuadros únicamente estimados. Un vehículo que cruza dos líneas aparece una vez en cada una.
- **SC-003**: Tras diez ciclos de retroceso/avance sobre los mismos instantes, los totales por línea son idénticos, independientemente de la velocidad elegida; no se muestra ningún cruce posterior al instante visible ni un cero para datos pendientes.
- **SC-004**: En un tramo completamente analizado de 30 segundos, la reproducción a 0,5×/1×/2× dura 60/30/15 segundos con una tolerancia del 5% en un equipo que sostenga la reproducción de referencia. Cambiar velocidad durante pausa conserva exactamente el cuadro visible. Se comprueba la sincronización en los mismos instantes fuente, sin afirmar rendimiento de análisis en tiempo real.
- **SC-005**: En 20 intentos controlados de reproducir o buscar fuera del tramo analizado a distintas velocidades, ninguno muestra cuadros no confirmados; alcanzar el límite conserva velocidad e intención de pausa/reproducción de forma consistente.
- **SC-006**: En 360/768/1440 píxeles, todas las tarjetas y acciones de edición/velocidad son alcanzables con teclado y tacto donde corresponda, sin desbordamiento horizontal de página; seleccionar una de diez líneas resalta inequívocamente su tarjeta y segmento.
- **SC-007**: En pruebas controladas de renombrado/recolorado, los valores confirmados se reflejan en tarjeta y segmento en menos de 1 segundo tras confirmación, sin cambiar cantidades ni reiniciar el análisis. Los colores iniciales de las diez líneas son diferentes y los duplicados se señalan antes de guardar.
- **SC-008**: Al reabrir un trabajo vigente se recupera el 100% de las líneas confirmadas con sus nombres/colores. Los casos de trabajo vencido, datos insuficientes y respuesta tardía no restituyen datos ajenos ni amplían su disponibilidad. Un caso anterior direccional pasa a ambos sentidos con cantidades verificadas o declara explícitamente que necesita nuevo análisis.
- **SC-009**: Al menos 4 de 5 personas de validación pueden crear dos líneas llamadas AV SIMÓN BOLIVAR y RUTA VIVA, cambiar un color desde una tarjeta y elegir 0,5× en menos de 3 minutos sin ayuda. Esta validación debe realizarse y documentarse después; no está acreditada por la especificación.
- **SC-010**: En un video de referencia con resultados conocidos, las operaciones de velocidad y líneas no cambian las detecciones, el resumen global ni la evidencia de inspección/exportación existente; las métricas de análisis y la reproducción con 1/10 líneas se registran por separado para detectar regresiones, con entorno y límites declarados durante la planificación.

## Assumptions

- Las líneas representan cruces en accesos, no rutas completas ni inferencia de giros entre vías. Conocer origen/destino, estimar caudal por tiempo y contar físicamente un vehículo tras perder su identidad quedan fuera de esta iteración.
- Se cuenta una vez por identidad local y línea/revisión, independientemente del sentido. La misma identidad puede aportar a varias vías; la suma de tarjetas no sustituye al inventario global.
- Se adopta capacidad inicial verificable de al menos 10 líneas; no se promete cantidad ilimitada. La planificación fijará y justificará el límite operativo admitido y sus mediciones.
- Nombres de ejemplo se conservan como los escribe el usuario; las etiquetas de línea deben ser distinguibles de los colores de clase de las cajas. Se emplean colores sólidos y tratamiento legible sobre escenas claras/oscuras, sin gradientes.
- Los ajustes de velocidad pertenecen al video abierto y se restablecen a 1× para uno nuevo; la recuperación tras recargar puede empezar a 1×. Las líneas confirmadas del mismo trabajo sí se recuperan mientras no venza.
- El conteo nuevo se realiza desde el inicio del tramo analizado disponible aunque la línea se configure más tarde. No se interpreta «crear línea ahora» como descartar los cruces anteriores.
- Las líneas que se superponen son válidas e independientes; borrarlas o moverlas no debe confundirse con filtros por dirección o clase seleccionados por el usuario.
- Se reutilizan detecciones y seguimiento existentes; no se cambian modelo, pesos, umbrales, hilos ni configuración privada. La tasa real de análisis y las pérdidas de seguimiento siguen limitadas por el entorno y la calidad del modelo.
- La implementación requiere cambios coordinados en la experiencia y el servicio de conteo para varias líneas/recuperación; los contratos, almacenamiento, compatibilidad y límites se definirán en plan, no en esta especificación.
- Esta iteración no añade nuevas exportaciones de estadísticas, no acelera el archivo descargado ni exige dibujar las nuevas tarjetas/líneas en el video exportado. Las exportaciones actuales conservan su comportamiento.
- Los pendientes de comparación larga y validación humana de iteraciones anteriores conservan su estado; esta especificación no acredita implementación, exactitud real ni pruebas de usuario.
