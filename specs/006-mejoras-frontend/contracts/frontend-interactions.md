# Contrato de interacción frontend — 006

**Estado**: diseño para implementar; no describe capacidades ya entregadas.

## Recorrido principal

1. Configurar sesión como en 005. Elegir archivo; previsualización e instrucciones, una acción fuerte «Analizar imagen».
2. Mostrar «Detección en curso»; evitar pulsaciones repetidas. No publicar porcentajes inventados.
3. Con respuesta válida, presentar imagen anotada y obtener original canónico protegido para evidencia. Controles sobre cada caja vehicular y lista equivalente; si hay elegibles, iniciar automáticamente enriquecimiento sobre `request_id`.
4. Mostrar «Enriquecimiento en cola/en curso» con progreso real. Se puede inspeccionar datos básicos mientras las demás secciones indican pendiente.
5. Tras completed, obtener todas las páginas, validar relación con fuente y detección, actualizar la ficha sin cambiar foco/selección. Nunca asociar por orden de llegada.
6. Un error de enriquecimiento conserva detección y evidencia válida; acción «Reintentar enriquecimiento» no repite detección. La pérdida ambigua de un POST no desencadena reenvío automático.

## Selección y semántica

- Overlay de botones reales sobre el área de la imagen, posición proporcional a dimensiones canónicas. Hover: cursor pointer y énfasis; foco visible; selección persistente distinta, `aria-pressed` y nombre «Inspeccionar detección N, clase».
- Lista paralela de vehículos con objetivos >=44x44 px, misma selección; accesible para cajas pequeñas o solapadas. Enter/Espacio activan el mismo resultado que clic/toque.
- Ficha en flujo: lateral en pantalla amplia y debajo en estrecha. Sin focus trap ni salto automático a la ficha. Nombre de región vinculado al vehículo seleccionado.
- Detección N es identificador de imagen; no sustituirlo por Track ID. Las cajas de otros actores siguen visibles sin ofrecer atributos de vehículo inexistentes.
- Si el overlay no cabe o se solapa, la lista debe seguir permitiendo acceder a todos los vehículos.

## Geometría y recortes

- Imagen W×H y caja `(x1,y1,x2,y2)`: left=x1/W, top=y1/H, width=(x2-x1)/W, height=(y2-y1)/H. Solo sobre el área renderizada de imagen, sin incluir letterboxing.
- Vehículo: región semiabierta válida del canónico. Placa: multiplicar su bbox relativa por ancho/alto de ese recorte vehicular; mismo truncado/clamp que la política de backend.
- Canvas solo para extraer los píxeles, no para controles interactivos. No recortar la imagen con anotaciones ni hacer mejora generativa.
- Si el canónico no se puede obtener o una caja es inválida, indicar «Recorte no disponible». Placa localizada pero ilegible conserva su crop; placa no localizada no genera uno.

## Presentación

Paleta de fondos grises claros, superficies blancas, texto azul oscuro y acento azul sólido. Sin gradientes. Tokens de espaciado 8/16/24/32 y tamaños tipográficos consistentes; no fijar alturas que trunquen contenido. Una acción principal por etapa, estado secundario legible.

- 1440 px: imagen predominante y ficha aproximada de 340 px, resto flexible.
- 768/360 px: una columna; controles envuelven, imagen proporcional y ficha con ancho completo.
- Contraste texto >=4.5:1, controles/foco >=3:1; texto 200%, movimiento reducido y estado comprensible sin color.
- Capturas requeridas: inicial, carga, detección, enriquecimiento, éxito, parcial, vacío, fallo, vencido y ficha con/sin placa en tamaños objetivo. Usar datos sintéticos y revisar antes de aceptar baseline.

## Errores y sesión

Errores HTTP se traducen por código a mensajes seguros y acción válida. No mostrar cuerpo crudo ni excepciones. 401/403 invalida evidencia afectada; 404 indica inaccesibilidad; 410 elimina la fuente/resultado afectado; 409 se traduce según fuente no lista/terminal; 503 conserva capacidades que sí sirven.

Una generación cambia con archivo, credencial, servicio o reset. Se cancelan fetch/timers, se eliminan resultados y se revocan URLs. Cancelación de trabajos remotos es independiente y no retrasa la limpieza. POST tardío que devuelve ID después de reset: cancelar con el cliente anterior cuando sea posible y jamás mostrarlo.

No afirmar que cerrar navegador garantiza cancelar en servidor: el TTL y janitor son la garantía de limpieza posterior. No usar localStorage/sessionStorage/IndexedDB para credenciales, placas o imágenes.

## Compatibilidad

Video/conteo conservan sus controles y flujos. El ciclo común de sesión debe limpiar también sus estados internos y recursos. Sus contratos no se cambian para el nuevo diseño de imágenes. No hacer que el antiguo EnrichmentPanel permita duplicar enriquecimiento de la imagen gestionada por el nuevo módulo; conservar su ruta de video.
