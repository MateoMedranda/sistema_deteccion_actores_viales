# Research —011 —2026-11-25

Investigación solo lectura; tres agentes de investigación despachados por la instrucción explícita de speckit-plan. No se ejecutaron modelos, pruebas largas ni cambios de producto. Todas las incógnitas de diseño se resuelven aquí; los umbrales de rendimiento siguen siendo objetivos a comprobar al implementar.

## R1 — Colección aditiva y contratos cerrados

**Decision**: Nuevos descriptor/colección y cantidades bajo /playback/count-lines; cuatro operaciones descritas en contracts/. Mantener010 intacto.

**Rationale**: backend/app/domain/video_detail_contracts.py y frontend/src/features/video-analysis/inspectionContracts.ts rechazan propiedades adicionales. El servicio actual tiene una configuración por trabajo y elimina sus eventos al editarla; no puede representar líneas independientes sin cambiar significado.

**Alternatives considered**: Ensanchar DirectedCount/Capabilities rompe consumidores estrictos; diez llamadas al endpoint anterior sobrescriben una misma fila. Diez pollers además multiplican tráfico.

## R2 — CAS de colección y IDs estables

**Decision**: PUT atómico de la colección completa≤10 por defecto/32 techo, con expected_revision y UUIDs del cliente. Validar todos los nombres/colores/geometrías y aplicar solo diferencias. Colección revision controla concurrencia; geometry_revision por línea controla su reducción.

**Rationale**: Un único CAS permite reservar nombres/colores/capacidad en la misma transacción y protege contra pérdida de cambios de otra pestaña. Los UUIDs permiten conciliar una respuesta perdida sin crear otra línea.

**Alternatives considered**: Endpoints por atributo/línea necesitan más contratos y coordinación global; crear IDs al responder puede duplicar líneas ante una respuesta perdida.

## R3 — Metadatos, revisión y eliminación

**Decision**: Nombre/color no borran trayectorias ni eventos. Cambiar geometría incrementa solo geometry_revision de su línea y retira sus estados anteriores. IDs eliminados dejan tombstone hasta TTL;128 admisiones de línea por trabajo por defecto. Colección guarda solo hash/expected_revision de la última mutación para repetir de forma segura una respuesta perdida inmediata; después se concilia con GET/CAS.

**Rationale**: Reintentos y resultados de reducer antiguos no deben resucitar configuraciones. Conservar todas las revisiones geométricas o recibos de cada rename produciría crecimiento innecesario. La unicidad de eventos se conserva para la revisión vigente.

**Alternatives considered**: Borrar por completo el ID permite reaparición por reintento; una cuota solo de líneas activas no acota los tombstones por sucesivas altas/bajas.

## R4 — Ambos sentidos y compatibilidad

**Decision**: Extraer la geometría de directed_counting.py o añadir una entrada bidireccional explícita; nuevo policy_version=finite-center-both-v1. El caso antiguo conserva su filtro de sentido. Solo centros medidos, segmento finito inclusivo, contacto sin evento hasta cambio de lado; una unidad por identidad/línea/revisión.

**Rationale**: Contar una caja cercana, una predicción o una prolongación generaría falsos aumentos. La taxonomía compartida reconoce Car/Bus/Truck/Big Truck/Motorbike/Van sin alterar nombres/IDs originales.

**Alternatives considered**: Quitar solo la flecha deja resultados direccionales; reinterpretar el valor antiguo falsea el historial y rompe contratos. Sumar tarjetas tampoco significa vehículos físicos distintos.

## R5 — Importación de línea anterior

**Decision**: POST import-legacy separado e idempotente cuando la colección esté vacía y el descriptor ofrezca una línea vigente. Guardar fingerprint, ID importado y marcador de operación incluso si luego se elimina esa línea. Conservar tablas anteriores y recalcular desde mediciones, sin tomar su total direccional.

**Rationale**: GET debe seguir siendo lectura. video_observation_provenance.measured puede declarar insuficiencia; en tal caso se conserva la geometría y se informa reanalysis_required.

**Alternatives considered**: Importación implícita durante GET añade efectos inesperados; reimportar al ver una colección vacía restaura líneas borradas. El cliente puede iniciar este POST automáticamente una vez al abrir un trabajo compatible, conciliando fallos.

## R6 — Worker justo y lock acotado

**Decision**: Un solo VideoDetailWorker, turnos round-robin y captura agrupada alineada;20 cuadros/200 pares cuadro-línea/2 MiB y presupuesto cooperativo5 ms. Geometría fuera del lock; commit con padre/generación/revisión/cursor todavía iguales. Leer una vez para líneas alineadas, sin dejar rezagadas otras. Limitar captura por frames, pares y bytes; no saltar un frame grande para avanzar cobertura.

**Rationale**: ProgressiveStore comparte lock y conexión con publicación/legacy. Repetir10×el lote actual de200cuadros dentro del lock perjudicaría análisis/consultas. Un vencimiento de presupuesto solo corta entre cuadros completos; el sistema operativo puede alargar un turno, por eso no es un plazo duro.

**Alternatives considered**: Un thread por línea crea contención; un scan por GET bloquea interfaz. No se justifica añadir otra base/cola externa ni cambiar journal como requisito de esta capacidad.

## R7 — Reloj y continuidad de reproducción

**Decision**: Módulo puro de ancla wall/source/rate; reanclar con el rate antiguo en el instante del cambio. Pausa/espera sin ancla activa, nuevo arranque desde cuadro pintado. Rate no entra en dependencias del efecto que crea decoder.

**Rationale**: ProgressiveVideoPlayer usa canvas/RAF; el cálculo actual es source+(now-wall)*1000. No hay elemento HTMLVideo de reproducción al que baste asignar playbackRate. performance.now ofrece reloj monotónico; la continuidad y la admisión siguen siendo decisiones locales del diseño. [MDN: performance.now](https://developer.mozilla.org/en-US/docs/Web/API/Performance/now).

**Alternatives considered**: Multiplicar todo el tiempo desde el ancla inicial por el nuevo rate produce saltos; reiniciar decoder pierde caché/posición. No cambiar timestamps de SourceDecoder: frame_index×1000 es identidad, no tiempo de reproducción.

## R8 — Prefijo, cuadros y cantidades

**Decision**: Mantener clampSeek/PTS/caches; consultar todas las tarjetas por start_us del cuadro efectivamente pintado y devolver un valid_until_us exclusivo por línea (mínimo del siguiente evento, cobertura y prefijo). La cantidad exacta se reutiliza solo dentro de ese intervalo, resolviendo la diferencia entre la tasa de cuadros y el poll400 ms; al agotarse, demanda coalescida con una sola petición en vuelo y100 ms mínimo entre inicios.0,25×–2× afecta solo al reloj. En2× se pueden omitir cuadros de presentación, nunca mediciones backend. La espera al límite limpia ancla; ocultar pestaña conserva la pausa explícita actual.

**Rationale**: sourceDecoder y frameCache tienen límites existentes; el rate no autoriza prefetch ilimitado ni cuadros sin anotaciones. El reducer puede tener coberturas distintas por línea: una línea pendiente no debe ocultar cantidades listas de las demás.

**Alternatives considered**: Cantidades locales basadas en cuadros mostrados pierden cruces a 2×; consultar el target futuro adelanta cantidades.

## R9 — Tarjetas, editor y fullscreen

**Decision**: CountLineBar dentro de progressive-viewer, antes del surface. Tarjetas con nombre completo accesible, color con borde legible, selección por UUID y control de color propio. Editor conserva pointer capture, arrastre del segmento/extremos y teclado, aplicado a la selección. Línea seleccionada con énfasis, sin flechas ni rótulos largos superpuestos.

**Rationale**: Ese contenedor es el root de fullscreen. El alto actual75vh de la escena debe ceder espacio a barra/controles. Las tarjetas resuelven selección de segmentos coincidentes y accesibilidad independiente de color.

**Alternatives considered**: Barra fuera del root desaparece en fullscreen; overlay tapa vehículos; usar el color como ID pierde la relación al recolorear.

## R10 — Nombres Unicode y colores

**Decision**: NFC, trim/colapso de espacios para display; clave única NFC+casefold.1–60 grafemas extendidos, hasta2048 bytes UTF-8 y1024 codepoints de techo de transporte, rechazando controles/bidi inseguros y nombres sin contenido visible. Backend: dependencia directa regex con \X y versión fijada en lock; frontend: Intl.Segmenter si existe, servidor como autoridad ante diferencias de Unicode. No usar maxLength HTML como límite de60 caracteres visibles. RGB#RRGGBB canónico mayúsculo, unicidad transaccional y32 colores por defecto distintos.

**Rationale**: Un grafema puede tener varios codepoints; Unicode recomienda combinar límite percibido y límite de bytes. regex documenta el matcher\X, y su distribución actual admite Python 3.12; no está instalado en este entorno aún. El conteo Unicode no se inventa con len/string.length. [Unicode UAX29](https://www.unicode.org/reports/tr29/), [regex: documentación del autor](https://pypi.org/project/regex/).

**Alternatives considered**: Contar UTF-16 falla con caracteres compuestos; NFC solo no cubre todos los grafemas. Una implementación manual incompleta crea discrepancias. En cliente antiguo sin Segmenter se permite validar en servidor, sin rechazar prematuramente un nombre válido ni bloquear toda la reproducción.

## R11 — Gateway, seguridad y vida temporal

**Decision**: Añadir únicamente las cuatro operaciones/path/query explícitas a ROUTES/classify;64 KiB para PUT/import, GET sin cuerpo, no-store y tope de respuesta2 MiB. Agregar familia a middleware bounded_video_detail y registrar recurso en detail_resources/purge. Parent/owner/generation/TTL antes de mutar y antes de confirmar reducer fuera del lock.

**Rationale**: app.web.proxy y app.main usan listas explícitas; crear solo la ruta backend no basta. Las tablas nuevas deben retirarse con ProgressiveStore. Logs incluyen IDs opacos/revisiones/cantidades/latencias, no nombres de vías, colores arbitrarios enviados, recortes, placas ni secretos.

**Alternatives considered**: Wildcard de proxy amplía superficie; TTL nuevo prolongaría datos sin autorización. Un404 de feature no disponible se trata localmente, sin sustituirlo por el antiguo conteo en un sentido ni retirar un video reproducible por error de capacidades.

## R12 — Pruebas y mediciones

**Decision**: Fixture011 nueva con las seis clases, ambos lados y varias líneas. Congelar una referencia de publicación antes de cambios; pruebas breves0/1/10 líneas y catch-up con resultados/entorno guardados. Medir reloj30 s a 0,5/1/2, diez seek-cycles y veinte intentos fuera de prefijo; ensayo humano4/5personas pendiente hasta realizarse.

**Rationale**: La fixture009/010 actual emite solo car y un sentido; no acredita las capacidades nuevas. El benchmark010 mide publicación, no inferencia ni reducción multilínea. Su referencia no debe sobrescribirse.

**Alternatives considered**: Reutilizar resultados anteriores como prueba de011, llamar FPS de YOLO al microbenchmark o cerrar gates humanos sin participantes son conclusiones no respaldadas.

## Fuentes de repositorio verificadas

- backend/app/services/{directed_count_service,directed_counting,video_detail_worker,video_progressive_store,video_observation_provenance,video_detail_access}.py
- backend/app/{domain/video_detail_contracts.py,domain/vehicle_taxonomy.py,web/proxy.py,main.py,core/lifespan.py}
- frontend/src/features/video-analysis/{ProgressiveVideoPlayer.tsx,sourceDecoder.ts,frameCache.ts,playbackPolicy.ts,useDirectedCount.ts,ProgressiveCountTools.tsx,useCountDraft.ts,inspectionContracts.ts}
- frontend/src/styles.css; backend/tests/e2e/serve_progressive_009.py; frontend/e2e/video-directed-count.010.spec.ts; backend/tests/performance/test_video_detail_overhead.py

Estas referencias son observaciones del checkout; los módulos nuevos que propone el plan aún no existen. No quedan decisiones bloqueadas para el usuario.
