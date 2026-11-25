# UI Contract: Video 010

## Ficha e inspección

- Compartir presentación de VehicleDetails de imágenes, con datos adaptados; conservar encabezado, cierre, recorte, atributos, placa, original/procesada y ampliación donde haya placa. Estado no disponible explica la capacidad, sin emitir endpoints de imagen desde video.
- `.progressive-details` no tendrá max-height ni overflow vertical de toda la tarjeta. La página maneja el desplazamiento; solo los visores de imagen/placa ampliados conservan scroll local propio.
- Escritorio a1440: video dominante y ficha lateral con ancho/tokens de imágenes. A768 y360: apilar sin recorte/horizontal de página, botones tocables y cierre accesible. Usar tipografía/espaciado compartidos y colores sólidos.
- Capturar la selección solo después de pausar y conocer el frame pintado: `(job,generation,track_id,frame_index)`. No convertir FPS ni usar un futuro frame pendiente. Cambiar vehículo/instante abre otro contexto; seek o reanudar cierran ficha. Cerrar no reanuda pausa manual.
- El hook mantiene selection_token local, aborta solicitudes anteriores y descarta respuestas cuyo token/contexto/generación ya no coincide. POST crea/reutiliza; GET solo completa datos. No POST periódico por result_revision/enrichment_revision.
- Vehicle asset_id se congela; plate asset_id aparece una vez. Blob/zoom original/procesada se asocian a inspection_id/asset_id y se conservan al completar atributos o leer otra revisión. No reset por objetos equivalentes o expires_at estable. Fallo temporal de una misma imagen conserva la válida con aviso; error de otro contexto nunca conserva imagen equivocada.
- 404 local muestra evidencia no disponible sin retirar video entero. Expiración/retirada del padre limpia blobs/resultados y detiene polling. Sin alternativa automática: opción con tiempo real requiere nuevo acto de selección.

- Si observation_kind=predicted, mostrar «Recuadro estimado» y «Confianza de la última medición»; para measured mostrar la confianza de la observación. No hacer pasar predicción por detección nueva.
- Preview de placa de video valida metadata `inspection-plate-preview-v1` contra contexto/asset, con geometría plate-crop. El adaptador de imágenes mantiene su DTO/parser propio; solo comparten controles y transformación visual.
- Un410 inspection_expired local retira únicamente esa ficha/crop, no la reproducción del padre todavía vigente; no reintentar POST para renovar el mismo contexto vencido.

## Editor y contador

- Tras seleccionar archivo, obtener primer frame local y habilitar editor ANTES del POST de análisis. Reutilizar arrastre de punto A/B y segmento y controles de teclado. Reemplazar archivo revoca URL y descarta borrador anterior.
- Flecha transversal a la línea, calculada en píxeles fuente y transformada a la pantalla. Botón «Invertir sentido»; etiqueta «Contar cruces en este sentido». No denominar A→B a desplazamiento entre lados cuando A/B son extremos.
- Conservar borrador hasta aplicar; indicar que cambiar línea/sentido recalcula cruces del prefijo. No cambiar el contador activo durante arrastre. Asociar la aplicación diferida al job/generation exactos tras aceptar carga.
- Acompañar el contador con una leyenda accesible de clases vehiculares conocidas; personas y clases sin catalogar no suman cruces. El resumen por clase mantiene categorías sin catalogar para revisión.
- Overlay superior derecho: «Cruces» + único total + flecha. Sin desglose bidireccional ni Track ID como cifra. Cuando varios cruzan a la vez, aumento igual al número de eventos.
- Consultas por posición incluyen revisión actual y token de navegación. Si la cobertura aún no alcanza el playhead, mostrar «Calculando cruces hasta …»; un valor anterior puede permanecer únicamente rotulado con su tiempo/configuración, no como total actual. Durante avance continuo no convertir una demora arbitraria de1s en vacíos intermitentes.
- Tras rewind, mostrar total histórico al confirmar nueva consulta. Sin acumulación local que duplique al reproducir. En pantalla completa la geometría/flecha e indicador conservan correspondencia.

## Resumen y exportación

- Sección «Vehículos detectados en todo el video» bajo reproductor/exportación, antes del editor. Total de identidades y cantidades por clase con color/etiqueta, estado parcial/final y cobertura. Diferente de «Vehículos de este fotograma» y de «Cruces».
- Mostrar categorías sin catalogar y nota de posible fragmentación de identidades; personas excluidas identificadas sin sumar a vehículos. Cambiar línea/playhead/ficha no modifica resumen final.
- Botón de exportación solicita `renderer=vehicle-labels-v1` y consulta esa misma variante. `VideoExport.tsx` y `services/apiClient.ts` necesitan un helper nuevo que valide job/renderer/ruta exactos y construya la descarga privada a través de /web-api; `nativeVideo(id)` antiguo sigue apuntando al MP4 legacy y no se reutiliza para esta variante. Un MP4 antiguo ready no se ofrece como etiquetado. Leer estado nunca solicita generación.
- Etiquetas de descarga «Clase · #TrackID», color compartido; sin placa OCR. Arriba de la caja si hay espacio, callout/líder si se desplaza. Mantener dentro del cuadro y nunca suprimir una etiqueta para resolver saturación; no se garantiza solapamiento cero en escenas físicamente saturadas.

## Evidencia de aceptación prevista

Capturas a360/768/1440 con ficha completa; 30s de polling con asset y zoom estables; misma identidad3s/20s; respuestas retrasadas después de seek/cierre; editor antes de upload; invertir/arrastrar por ratón/teclado/toque; dos recorridos y cinco saltos; resumen con/sin línea; cuadros decodificados del MP4 con Camión/Autobús/bordes/densidad. Deben ejecutarse durante implement; no son resultados de esta fase.
