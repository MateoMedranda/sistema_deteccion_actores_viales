# Modelo de datos —011

Diseño futuro; no se crean tablas ni migraciones en plan. Nuevas tablas en la base/conexión de ProgressiveStore; no se modifica el significado de p_directed_count_* ni del inventario. Identificadores de trabajo conservan el formato vigente; UUID de generación/línea, enteros seguros0..2^53−1 y tiempos fuente en microsegundos.

## 1. CountLineCollection / p_count_lines_collection

Una fila por `(job,generation)`; referencia lógica a p_video, cuyo owner/TTL son autoridad.

| Campo | Significado |
| --- | --- |
| revision | Revisión de configuración,0 si aún no existe; aumenta solo al cambiar el conjunto, nombre/color o geometría |
| admitted_total / next_ordinal | IDs distintos admitidos desde el inicio y orden estable de creación; no bajan al eliminar |
| last_expected_revision / last_mutation_hash | Recibo mínimo de la última PUT aplicada; no conserva datos de reconocimiento ni un historial ilimitado |
| legacy_import_state | none/offered se resuelven por lectura; imported queda persistido después del POST, incluso al borrar la línea importada |
| legacy_line_id / legacy_fingerprint | UUID estable importado y huella del segmento anterior; nunca su cantidad direccional |

La respuesta GET sin fila devuelve revision 0, admitted_count 0 y colección vacía, sin INSERT. Descriptor anuncia admitted_count incluyendo tombstones para explicar el agotamiento de admisiones antes de intentar otra alta. Ofrecer importación solo inspecciona metadatos legacy autorizados; no inicia modelos ni reconstrucción. Los GET no actualizan last_seen, cuotas, cursores, hash ni TTL.

## 2. CountLine / p_count_lines

Clave `(job,generation,line_id)`. Campos: name, name_key, color, segment (extremos normalizados), ordinal, geometry_revision≥1, cursor (próximo índice), covered_until_us, error_code y deleted. Un ID tombstoned no puede admitirse de nuevo para esa generación.

- `name`: normalizar NFC, eliminar espacios exteriores y colapsar espacios Unicode redundantes; conservar letras/acentos/caja. `name_key`: NFC+casefold del nombre normalizado, sin quitar tildes. Rechazar contenido vacío/no visible, controles o controles bidireccionales inseguros; ZWJ/ZWNJ válidos dentro de secuencias visibles no equivalen a un nombre vacío.
- Límite de1–60 grafemas extendidos; hasta2048 bytes UTF-8 y1024 codepoints de techo de transporte. El techo no sustituye al cómputo de grafemas. Contar con regex\X, no len; fijar dependencia en lock durante implementación. Casos compuestos/descompuestos y emoji se cubren con corpus de prueba. Autoridad semántica backend ante diferencias Unicode del navegador.
- `color`: #RRGGBB mayúsculo; se aceptan variantes de caja, se rechazan formatos abreviados, alfa, CSS arbitrario/gradientes. Único entre líneas activas por valor RGB, no por texto original. El descriptor expone32 colores candidatos únicos; elegir el primer libre. Contorno y texto independiente garantizan legibilidad sin convertir el color en ID.
- `segment`: x/y finitos0..1; extremos distintos. La geometría se calcula en píxeles fuente para el segmento inclusivo, preservando la tolerancia vigente1e−6píxel para lado y1e−12para intersección. Dos líneas pueden tener la misma geometría y conservar su identidad propia.
- Orden de tarjetas: ordinal de primera admisión, no orden incidental del array PUT ni color/nombre. Reordenar el array sin cambiar campos no constituye edición.
- Capacidad activa10 por defecto, configurable10–32. Admitidas128 por defecto, configurable≥activas hasta1024. Deleted mantiene solo ID, ordinal y metadatos mínimos necesarios como tombstone; borrar nombre/color/segment y filas de trabajo de esa línea. No exponer tombstones en descriptor.

## 3. Estado de trayectoria / p_count_lines_tracks

Clave `(job,generation,line_id,geometry_revision,track_id)`. Payload mínimo point/side/contact/counted reutiliza la geometría comprobada, con modo ambos sentidos explícito. Fuente exclusiva: video_observation_provenance.measured; un cuadro predicho no altera trayectoria ni votos del contador. Medición confirmatoria evalúa la clase elegible usando el catálogo compartido actual; persona/desconocido no suman.

Todas las mediciones conservan posición/lado aunque la clase no sea elegible. Un contacto conserva la referencia de lado hasta confirmar/deshacer la transición. Un cruce excluido por clase no consume un futuro cruce elegible. La trayectoria que empieza sobre la línea aún no acredita de qué lado venía. Conteo no mide presencia dentro de una caja ni intersección de su borde: usa el centro medido.

## 4. Evento / p_count_lines_events

Clave `(job,generation,line_id,geometry_revision,track_id)`; confirming_frame_index, time_us=start_us de confirmación y class_key_at_crossing canónica inmutable. Índice compuesto `(job,generation,line_id,geometry_revision,time_us)` para total histórico count(time_us<=at_us).

Cada identidad suma una vez en una línea/revisión, aunque oscile o vuelva a cruzar; la misma identidad puede tener un evento en varias líneas. Normalizar Big Truck→big_truck y Motorbike→motorcycle sin alterar observación original. No reevaluar un evento con clasificación posterior, OCR ni votos de inventario.

## 5. Mutación atómica y revisiones

PUT `{generation,expected_revision,lines}` representa todo el conjunto confirmado, no un PATCH parcial ni una orden de acumular sobre el conjunto anterior. Máximo32 objetos en transporte; límite efectivo del descriptor se aplica además. Línea omitida equivale a eliminación explícita del conjunto que el cliente confirmó.

1. Validar padre/propietario/generación/TTL, cuerpo cerrado y normalización. Comparar expected_revision con revisión actual dentro de la transacción compartida.
2. Para una repetición inmediata con revisión antigua, aceptar solo si coincide last_expected_revision+hash canónico de la última mutación y la colección sigue exactamente en su revisión resultante; retornar descriptor actual sin cambios. En otra condición,409 count_revision_changed.
3. Validar IDs únicos, nombres/colores únicos y capacidades del conjunto final antes de escribir; verificar tombstones y admisiones. Hash canónico ignora orden del array y normaliza valores; incluye generación, expected_revision y cada campo confirmado.
4. Si el conjunto normalizado es idéntico y expected_revision es actual: no-op, sin incremento ni recalcular. Si cambia, aumentar revision una vez. Nuevos IDs reciben ordinal y geometry_revision 1. Metadatos solos conservan geometry_revision, cursor, trayectorias y eventos. Geometría distinta incrementa geometry_revision y reinicia únicamente su cursor/cobertura/estados/eventos desde el inicio del tramo retenido.
5. Al eliminar, retirar trabajo y conservar tombstone; nunca reutilizar su UUID. Las otras líneas conservan sus estados. Intercambiar colores/nombres entre líneas es una operación atómica válida si el conjunto final es único: validar antes, usar actualización temporal interna dentro de la misma transacción si se requieren índices únicos; nunca exponer estados intermedios.
6. Cualquier fallo revierte la transacción completa. El cliente conserva borrador y última colección confirmada; ante409 recupera descriptor y presenta conflicto, sin sobrescribir automáticamente cambios ajenos.

La revisión de colección no avanza al reducir cuadros. Un rename durante geometría fuera del lock no invalida el trabajo si geometry_revision/cursor siguen iguales; el commit no se basa solo en la revisión de metadatos. No conservar revisiones geométricas antiguas indefinidamente: la API nueva consulta historia temporal de la revisión actual, no versiones de configuraciones ya sustituidas.

## 6. Reducción, cobertura y respuesta

Round-robin entre trabajos/líneas. Bajo lock capturar padre+líneas/cursor y hasta20 cuadros,200 pares cuadro-línea y2 MiB de payload. Agrupar líneas de cursor alineado para leer/decodificar JSON una sola vez. Calcular fuera del lock en un turno con presupuesto cooperativo5 ms; confirmar solo cuadros completos y comprobar antes de commit padre no retirado/vencido, generación, existencia no eliminada, geometry_revision y cursor iguales. Datos obsoletos se descartan sin tocar las otras líneas.

Un cursor avanza también por cuadros predichos sin crear eventos; covered_until_us llega al end_us del último cuadro íntegro confirmado. Errores de procedencia/límite hacen unavailable solo a las líneas afectadas, sin hacer fallar el video ni saltar huecos. Reservar tiempo para publicación/inspecciones/inventario y dar oportunidad a todos los trabajos; no multiplicar200cuadros dentro del lock por cada línea.

Cada CountValue lleva line_id/geometry_revision/status/result_scope/covered_until_us/total/error_code. Ready exige estrictamente at_us<covered_until_us y at_us<available_until_us; total puede ser0 solo cuando se acredita cobertura. Pending y unavailable devuelven total=null. `result_scope`: building durante análisis/catch-up, final solo con análisis completo y línea totalmente cubierta, partial si el trabajo termina por fallo/cancelación con prefijo válido. Una línea pendiente no invalida las otras.

GET counts exige revision de colección actual y una sola generación/posición para todas las tarjetas; at_us se corresponde al cuadro pintado. Con prefijo vacío se admite at_us0 y solo pending/null; el extremo exclusivo no es un instante disponible. Buscar al futuro devuelve409 interval_not_ready. Las tarjetas pueden cubrir prefijos distintos sin usar una cantidad del futuro.

## 7. Importación de010

POST import-legacy con generation/expected_revision. Permitido por primera vez solo si colección vacía y hay segmento anterior vigente; el CAS protege creación concurrente. Admite el UUID importado determinista de esa generación, Línea 1 y primer color libre. Conservar original legacy sin mutarlo; guardar marcador/fingerprint. Si una edición legacy anterior cambia luego, no sobrescribir automáticamente la importación.

El primer POST hace configuración y cursor inicial, no reducción completa. Repetir el POST después de imported devuelve el descriptor vigente sin nueva línea, incluso si la línea importada se eliminó; no restablece nada. En colección no vacía sin importación previa:409 legacy_import_conflict. Sin candidato:409 legacy_line_unavailable. Generación/TTL/autoridad siempre se validan primero. Falta de procedencia al reducir se declara reanalysis_required, no copia de totales antiguos.

## 8. Contexto cliente y velocidad

Colección confirmada, borradores por line_id y selección son estados distintos. Presentación revisada al confirmar nombre/color/geometría; el canvas usa un número de revisión y selección para repintar, no JSON.stringify de todas las líneas por RAF. Initial drafts se envían como una mutación conciliable; marcar aplicado únicamente tras confirmación o GET equivalente.

La respuesta del snapshot debe coincidir con job/generation/revision, IDs y geometry_revision esperados, secuencia de consulta y el at_us enviado en esa petición. Esta comprobación de respuesta no exige igualdad entre snapshot.at_us y el start_us de cada cuadro que se pinte después. Durante reproducción ordinaria, un total ready sigue siendo exacto y puede mostrarse mientras el cuadro pertenezca a [snapshot.at_us,line.valid_until_us), según §10. Fuera de ese intervalo se muestra actualizando solo para esa tarjeta y se solicita otra consulta agregada. Un seek nuevo o cambio de generación/revisión invalida respuestas en vuelo del contexto anterior; editar geometría o eliminar una línea nunca permite reaparecer cantidades o tarjetas antiguas.

Velocidad en memoria por video: presets0.25/0.5/0.75/1/1.25/1.5/2; inicio 1. Ancla opcional wall_ms/source_us/rate, intención de reproducir independiente de buffering. Al cambiar rate en marcha, calcular fuente con rate anterior al mismo now y reanclar; pausado/esperando conserva cuadro y ancla vacía. Ocultar pestaña o workspace pausa como hoy; conservar rate y no recuperar tiempo oculto. Reabrir puede iniciar1×, como permite spec. Decoder/PTS/fuente/exportación permanecen intactos.

## 9. Privacidad y limpieza

Registrar el nuevo servicio en ProgressiveStore.detail_resources e incluir tablas en purge de retirada/TTL y recuperación de inicio. Todo commit de reducer comprueba que no publicó tras retirada. Solo tombstones mínimos permanecen hasta el TTL padre; después se retiran también. No ampliar fechas por polling/edición/importación. Sin archivos nuevos ni duplicación de decodificación/modelos. Logs: IDs opacos/revisiones/contadores agregados/latencias/códigos, sin nombres de vías, placas, rutas, recortes ni credenciales.


## 10. Intervalo de validez exacta de cada cantidad

Para un snapshot listo en at_us, valid_until_us es el mínimo entre el siguiente evento de esa línea estrictamente posterior a at_us (si existe), covered_until_us y available_until_us. Por lo tanto total es exactamente válido para cualquier cuadro pintado con start_us dentro de [at_us,valid_until_us), sin mostrar cruces futuros ni exigir una petición por cuadro. La cobertura ya confirmada no admite inserciones retrospectivas de eventos.

Si pending/unavailable, total=null y valid_until_us=at_us: no hay intervalo reutilizable. Un ready exige at_us<valid_until_us≤covered_until_us y≤available_until_us. Al cruzar el extremo exclusivo, solo esa tarjeta muestra actualizando mientras llega el nuevo snapshot. Buscar antes del at_us base o fuera de cualquier intervalo conocido requiere consulta nueva; una respuesta de un seek anterior no repinta el contexto siguiente.

Snapshot/cobertura/evento siguiente se leen bajo el mismo lock en una lectura coherente. El cliente puede aceptar una respuesta de un cuadro anterior durante reproducción ordinaria si su intervalo cubre exactamente el cuadro actual; no acepta respuestas tardías de otra revisión/seek/generación. Un poller cada400 ms más demanda coalescida al agotar intervalo/seek, máximo una petición simultánea y100 ms entre inicios, evita la contradicción entre30 cuadros/s y cantidades exactas consultadas por red. Si se pierde conexión y el cuadro sale del intervalo confirmado, no se conserva un número como actual sin advertencia.

Al reducir configuración por debajo de las líneas/admisiones ya existentes, no borrar datos ni bloquear cambios de nombre/color o eliminaciones: rechazar solo altas netas mientras se exceda el nuevo límite. La colección y sus IDs permanecen recuperables.


Para respetar el límite de captura2MiB antes de materializar payloads, consultar longitudes y acumular bytes al capturar; no hacer fetchall de20payloads de tamaño desconocido para comprobar el límite después. El límite se refiere al payload adicional de trabajo, no a una afirmación sobre toda la memoria de SQLite.
