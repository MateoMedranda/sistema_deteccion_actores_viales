# Contratos de interfaz y reproducción —011

## Composición

Dentro del root fullscreen `progressive-viewer`: título/estado, `CounterBar`, escena sin contador numérico superpuesto y controles con `PlaybackRateControl`. La ficha de vehículo continúa al lado según el layout existente. El editor de primer fotograma conserva su sección inferior; la selección de tarjeta sigue disponible en fullscreen. Si no hay líneas, la barra muestra una indicación breve para añadirlas, sin crear una por GET.

Tarjeta con nombre consultable completo, swatch, cantidad/estado, botón de selección y edición de nombre/color/eliminación. Colores sólidos y texto neutro; tarjeta/segmento seleccionado usan borde/indicador además del color. Controles de44px mínimo, etiquetas accesibles por nombre de línea, foco visible y sin depender solo de hover. Para diez tarjetas en360/768/1440 usar filas adaptables o grupos accesibles; sin desbordamiento horizontal de página. En fullscreen reservar alto para barra/controles y encajar escena en el restante, sustituyendo el supuesto fijo75vh.

## Editor y borradores

`useCountLineDrafts(file)` conserva captura local del primer fotograma, revocación de URL y reset al cambiar archivo. Drafts por UUID y selección, independientes de la colección confirmada del servicio. Dibujar/arrastrar extremos o segmento completo conserva pointer capture y clamp; keyboard Arrow/Shift+Arrow ajusta solo la selección. Tarjetas/lista permiten seleccionar segmentos coincidentes sin mover varios.

Nombre provisional «Línea N» y primer color libre de los32candidatos; crear no excede límites anunciados. Antes de upload usar los defaults versionados compatibles con el contrato y reconciliar con el descriptor del trabajo antes de confirmar. Color ya usado muestra explicación; no reemplaza color de otra línea. Validación local de grafemas con Intl.Segmenter si está disponible; en ausencia, deja decidir al servidor sin usar string.length como límite60. Conflicto de nombres también se resuelve con validación autoritativa del conjunto.

Confirmar produce una PUT del conjunto completo esperado; no emitir una PUT por cada movimiento de puntero. Aplicar borradores iniciales solo se marca terminado después de respuesta confirmada o GET equivalente. Una respuesta perdida no deja initialDraftApplied=true sin líneas guardadas. Mantener draft para corregir conflicto/reintentar, sin sobrescribir cambios de otra pestaña automáticamente.

## Consulta agregada

`useCountLines` descubre configuración y límites; `useCountSnapshots` hace una consulta agregada cada400 ms mientras haya trabajo activo/visible y a demanda tras seek o agotamiento de intervalo válido, coalesciendo motivos y manteniendo una sola petición en vuelo con separación mínima100 ms. La actualización es por conjunto; ninguna tarjeta inicia su propio bucle. Nunca un hook/poller por tarjeta. Cuando cambia la revisión, recuperar descriptor/line IDs antes de mostrar cantidades. Si solo cambia metadata, conservar los eventos del servidor; una respuesta para la colección anterior no puede relabelar una tarjeta nueva.

La posición para counts es start_us del cuadro pintado, no target del reloj. El hook filtra job/generation/revision/line_id/geometry_revision/at_us/secuencia y aborto. Durante reproducción ordinaria, una respuesta anterior puede mostrarse solo si el cuadro pintado pertenece a [snapshot.at_us,line.valid_until_us): su cantidad sigue siendo exacta hasta el próximo evento/cobertura/prefijo. Fuera del intervalo, mostrar actualizando solo para esa tarjeta y solicitar snapshot coalescido. Un seek nuevo invalida respuestas en vuelo de la navegación anterior; dentro de un intervalo confirmado puede reutilizarse su cantidad exacta. No exigir igualdad con el cuadro de origen para todos los cuadros de reproducción, ni conservar números fuera de validez como actuales. Una tarjeta pending/unavailable no oculta otras ready. Un404 de capacidad mantiene video e inspección disponibles; no sustituye la feature por una vía direccional.

Primera apertura de colección vacía con legacy_import.offered: un POST import-legacy serializado y conciliable. Repetir/reconectar no duplica. Imported con ID borrado no activa de nuevo. Error de importación indica si faltan observaciones o conflicto; no presenta el total antiguo con otra etiqueta.

## Reloj puro

Datos: rate∈{0.25,0.5,0.75,1,1.25,1.5,2}; ancla opcional wall_ms/source_us/rate; intención de reproducción independiente del estado wait. Muestreo en marcha: source_us+(now−wall_ms)*1000*anchor.rate. Reanclar con rate viejo al mismo now antes de establecer el nuevo. Si hay espera/pausa no existe ancla en marcha y cambiar rate conserva exactamente el cuadro visible.

Mantener1× al iniciar video nuevo; conservar selección al cambiar pestaña del mismo trabajo. Ocultar documento/inactivar workspace pausa como actualmente; regresar no acumula tiempo oculto. Resume/seek/buffering establecen ancla nueva desde posición admitida/pintada, sin sumar el tiempo transcurrido esperando datos.

No agregar rate a dependencias que recrean SourceDecoder/cache. No cambiar timestamps de identidad frame_index×1000, PTS/timebase ni los índices de observaciones. No extender límites28frames decodificados/8MiBcache codificada/16MiB anotaciones por intentar sostener2×. Se pueden omitir cuadros de presentación con sus propias anotaciones correctas; el servidor sigue reduciendo todas las mediciones. En cada dibujo respetar prefix admission y sourcePTS equivalentes.

Control accesible de velocidad junto a reproducción; cambiar mientras está pausado no reanuda. Cambiar rate no solicita OCR, exportación ni detección y no cierra la evidencia seleccionada en pausa. El bloqueo de búsqueda futura sigue activo. Al alcanzar el límite, indicar espera con rate conservado; solo retomar intención previa si el usuario no pausó explícitamente.

## Canvas y consistencia

Dibujar todos los segmentos confirmados con sus colores y contorno oscuro/claro, enfatizando selección. Nombres completos residen en tarjetas para no tapar vehículos. Repintado por presentationRevision/selección, sin JSON.stringify de todo el conjunto en cada RAF. Eliminar los caminos nuevos de directionArrow, su botón/copy y overlay numérico único; mantener APIs de compatibilidad anteriores aisladas.

No cambiar flujo de imagen, ficha compartida, inspección exacta, inventario o video exportado. La velocidad no altera duración/contenido de la descarga. Regresiones010 que esperaban flecha se actualizan solo para UI nueva, conservando tests de servicio direccional como compatibilidad.
