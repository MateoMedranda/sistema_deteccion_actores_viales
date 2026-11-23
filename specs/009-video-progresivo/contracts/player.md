# Reproductor — contrato de interacción 009

## Salida visible y decisión corregida durante implementación

Solo canvas dibuja píxeles y cajas. La prueba bajo carga mostró que mediaTime de un video nativo podía corresponder a una textura distinta al copiarla al canvas. Se sustituyó esa estrategia por VideoDecoder/WebCodecs con VideoFrame inmutable y lectura MP4 acotada mediante mp4box 2.6.0. No se expone un video original como alternativa visible.

El lector obtiene por Range los metadatos y muestras AVC; no descarga el archivo completo para iniciar. Ordena las muestras por CTS, aplica una única edición normal a velocidad1 y asigna una identidad de presentación estable a cada muestra. El timestamp interno del chunk codifica esa identidad; no es el reloj de reproducción. Antes de dibujar se exige identidad exacta del VideoFrame, frame_index publicado y coincidencia del PTS relativo con start_us (tolerancia de redondeo1us). El reloj visible siempre usa los intervalos de la API de origen, incluso para VFR.

Un cuadro solo se dibuja con sus anotaciones completas, dentro del prefijo confirmado y de la generación vigente. Canvas congela la salida ante JS ocupado. Al navegar se retiran imagen/cajas anteriores hasta recuperar el cuadro correcto. La transformación de orientación y las coordenadas de cajas/hit targets comparten el plano publicado. Se conservan colores sólidos y la lista DOM accesible.

## Reloj, controles y recuperación

Separar intención manual de reproducir/pausar del reloj que puede avanzar. Inicio y reanudación automática exigen buffer_seconds (5s predeterminados); una fuente terminal permite su cola corta. Se conserva 1x y se detiene el reloj cuando faltan cuadros/anotaciones o se alcanza el límite. Una pausa manual nunca se revoca por crecimiento del prefijo.

La barra muestra posición, duración estimada/confirmada y cobertura disponible/pendiente. Su extremo autorizado es last_frame_start_us, no el final exclusivo del último intervalo. Home, End, flechas, PageUp/PageDown, toque y acciones MediaSession usan el mismo clamp. Fullscreen pertenece al contenedor con controles propios.

Desconexiones recuperables reconsultan el mismo trabajo con backoff1/2/4/8s, sin POST adicional. Poll visible500ms con una petición de estado en vuelo. Ocultar el modo pausa; el vencimiento sigue activo aunque esté oculto. 401/403/404/410, limpieza o sustitución abortan lecturas, liberan frames/URLs y retiran la vista; respuestas tardías no la restauran.

## Límites de memoria y formato

- Anotaciones:16MiB y30s acumulados, ensamblado completo de partes y hasta4 ventanas en vuelo.
- Bytes MP4:8MiB LRU por bloques; metadatos recibidos para parsing<=16MiB.
- Posters de navegación:<=4 y<=16MiB estimados de píxeles.
- Cuadros activos:<=28, más los posters; todos los VideoFrame se cierran al expulsar o retirar.
- Cada lectura de fuente<=8MiB y requiere Range206, Content-Range exacto y ETag de la generación.

Se valida VideoDecoder.isConfigSupported para el AVC concreto. MP4 fragmentado, múltiples ediciones no vacías, cambios de velocidad y matrices no ortogonales se rechazan para esta vista. Se informa incompatibilidad y se mantienen consultables los datos. WebKit de prueba en Windows no ofrece VideoDecoder: se comprobó esa salida segura, no se acredita reproducción en ese entorno.

## Verificación

Ver validation.md y evidence/browser-metrics.json. Las pruebas con cuarenta segundos sintéticos verifican primer buffer, píxeles, treinta saltos, una ventana de5s a1x, JS ocupado, estados y respuesta tardía. Esto no reemplaza medición prolongada con modelos reales, historial expulsado ni la prueba con cinco participantes.


## Inspección selectiva y conteo

La selección pausa y hace POST idempotente para ese Track ID; repetir una selección reusa la misma solicitud. La ficha a la derecha mantiene jerarquía de Imagen y separa estados de consulta y validez de placa. La alternativa a las cajas es un desplegable de vehículos del fotograma debajo de los controles, sin lista sobre la ficha. No hay barra global de enriquecimiento.

La sección inferior captura únicamente un canvas confirmado; el usuario dibuja dos puntos o usa rangos etiquetados de teclado. La línea confirmada se dibuja en el plano del canvas principal y el contador superior derecho consulta acumulados del instante reproducido. Saltar invalida el contador anterior hasta recuperar el correspondiente; no se muestra el total de un instante futuro. Desactivar elimina la línea y el contador. El editor no reproduce un segundo video ni ejecuta otra detección.


El editor muestra automáticamente el primer cuadro confirmado, sin pulsar «Usar fotograma actual». La copia usa el decoder activo y está acotada; los controles originales de dibujar/arrastrar se restauran con Pointer Events y pointer capture. El hit test del segmento permite trasladar ambos puntos conservando su distancia y limitando la traslación a la imagen. Los extremos permiten teclado y arrastre individual. Borrar línea también desactiva el conteo activo.
