# Propuesta revisada: inspección de enriquecimiento en video

**Iteración**: [008 — Exploración de imágenes y video](spec.md)
**Estado**: Revisada contra el código de008 y sus recorridos controlados. No es una función implementada ni amplía el alcance de FR-025.

## Interacción propuesta

1. Reproducir el video con contornos limpios y colores por clase, sin nombres o identificadores tapando los vehículos.
2. Pulsar **Pausar para inspeccionar**. Conservar el cuadro y tiempo visibles y mostrar en una zona exterior los vehículos presentes en ese instante.
3. Elegir un contorno o el vehículo de la lista equivalente. Destacar su contorno sin ocultar la escena y abrir una ficha lateral; en móvil, usar un panel bajo el reproductor.
4. Mostrar track ID, clase y enriquecimiento disponible. Separar el tiempo seleccionado del tiempo del cuadro usado como evidencia de atributos/placa; una lectura representativa no es lectura en vivo.
5. Ofrecer **Volver a reproducir**. La selección puede seguir marcada mientras la trayectoria exista; la ficha indica si describe una selección retenida que ya no está presente. No se sigue un vehículo nuevo reutilizando datos del anterior.

Consultar o pausar utiliza resultados ya calculados, sin ejecutar detector ni OCR de nuevo. La lista proporciona una alternativa para cajas pequeñas, solapadas o difíciles de tocar.

## Comportamiento al cambiar el tiempo

- Una búsqueda temporal pausa la inspección y vuelve a resolver qué identidades existen en el cuadro seleccionado; descarta respuestas de tiempos anteriores.
- Si el vehículo no está presente, se indica explícitamente. La ficha no se coloca sobre un vehículo distinto.
- Si el enriquecimiento aún está pendiente o falló, se mantiene esa indicación junto al contorno autorizado; no se inventan atributos.
- Si vence la fuente o se rechaza el acceso, se retiran cuadro y datos, incluso con el video pausado.
- Teclado y toque permiten la misma selección; el foco permanece controlable sin tener que perseguir cajas en movimiento.

## Dependencias para una iteración posterior

- Correspondencia verificable entre tiempo/cuadro mostrado, orientación/tamaño del medio y trayectorias. La precisión depende de esa correspondencia, no solo de disponer de track IDs.
- Posiciones de contornos e identidades consultables para el instante pausado y acceso autorizado a resultados por fuente/track ID.
- Diferenciar la geometría presentada de las observaciones originales y de la evidencia elegida para enriquecimiento; conservar las tres asociaciones.
- Acceso temporal acotado a los medios necesarios, si se añaden nuevas vistas de evidencia, sin ampliar retención ni generar historial.
- Verificación de pausa, búsqueda temporal, cruces, pérdidas del seguimiento, solapamientos, accesibilidad, vencimiento y coste antes de comprometer la implementación.

## Entrega de008 frente a propuesta

008 entrega navegación, configuración administrada, zoom de escena, presentación de video, enriquecimiento automático, progreso y consulta por lista/ficha junto al reproductor. Esta propuesta añade después la selección directa sobre un cuadro pausado y su resolución temporal. La entrega real usa reproducción nativa autenticada por Range, lista paginada de25 y ficha por track_id, con evidencia i/fps cuando la metadata CFR está confirmada. No hay endpoint de recorte de video ni índice temporal de contornos presentados.

Se recomienda añadir después un índice autorizado y acotado (videoJobId,frame_index,track_id,bbox_presentada), consultable por intervalo y purgado con el mínimo TTL, asociado a la observación raw. Al pausar/buscar se consultará sin inferencia; el tiempo se convertirá al cuadro CFR tras seek completado. La ficha explicitará el cuadro de evidencia de cada campo. Enter/Espacio y lista equivalente de44px evitarán depender de cajas pequeñas. En móvil se propone un panel inferior con devolución de foco al cerrar. Una generación temporal descartará respuestas de búsquedas anteriores. Estas son dependencias futuras, no rutas de008.
