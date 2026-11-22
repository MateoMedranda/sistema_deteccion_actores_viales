# Reproductor — contrato de interacción 009

## Salida visible

Video fuente silenciado como decodificador, sin controles nativos, foco, PiP, cast ni fullscreen propios. Mantenerlo decodificando de manera compatible con los navegadores objetivo; no asumir que display:none conserva callbacks. Solo el canvas visible dibuja video y cajas juntos. Nunca mostrar el video crudo para remediar un fallo del canvas; informar indisponibilidad de reproducción y mantener resultados consultables.

En requestVideoFrameCallback, tomar mediaTime y resolver el intervalo confirmado. Solo dibujar si job/generation siguen vigentes, el cuadro pertenece al prefijo autorizado y sus anotaciones se reconstruyeron completas. Píxeles, cajas, hit targets y etiqueta temporal se actualizan juntos. Una callback tardía fuera del prefijo no dibuja; pausa el decoder, conserva el último cuadro válido y entra en espera. Un bloqueo de JS congela salida, no deja visible un cuadro futuro.

No repetir suavizado tras un salto. Las coordenadas de presentation bbox se transforman con la misma geometría/rotación y object-fit usada para los píxeles. Canvas tiene descripción accesible y una lista DOM de vehículos ofrece alternativa de foco, teclado y toque; no construir cientos de botones sobre vehículos pequeños si reduce la legibilidad.

## Estado

Separar userIntent=play|pause de phase=initial|playing|waiting-analysis|loading-annotations|manual-pause|partial-terminal|retired. También guardar posición admitida, watermark autoritativo, cobertura local, generación, activeMode y motivo de espera.

- Inicio: botón reproducir habilitado tras5s disponibles; tail terminal permite menos. El primer clic satisface la política de reproducción del navegador.
- Llegada de límite: no cambia posición ni selección. Se pueden obtener por anticipado las siguientes páginas, sin superar presupuestos de caché.
- Espera automática con userIntent=play: pausa decoder; reanudar al existir5s desde la posición, o tail terminal. Un clic en pausa cambia intención y bloquea reanudación automática.
- Seek dentro del prefijo: validar destino antes de asignar currentTime, pausar, limpiar cajas anteriores, invalidar fetch obsoletos, recuperar todas las partes del intervalo, dibujar destino y restaurar intención previa. No repetir inferencia.
- Seek al extremo exclusivo: usar last_frame_start_us del cuadro final, no el número available_until_us como si fuera un cuadro reproducible.
- Seek fuera: clamping al último cuadro permitido y anuncio discreto de que falta análisis; la barra y etiqueta nunca adelantan la posición visible.
- Cambiar de modo pausa el decoder; volver conserva posición e intención, pero no reanuda hasta que el modo esté activo y el usuario no haya pausado. Cambiar archivo o limpiar destruye estado y retira fuente.
- Clic en caja/lista pausa e identifica (job,generation,track_id). Cerrar ficha no deshace la pausa manual; actualización de datos no modifica posición.
- Error técnico conserva prefix/ficha válidos, indica parcial y permite reproducir tail. Cancelar/revocar/expirar borra canvas, src, blobs de evidencia, caché y selección e invalida callbacks.

## Controles

Barra con posición, tramo disponible y zona pendiente; duración confirmada/estimada, tiempo de análisis y estado de enriquecimiento diferenciados. Teclado: espacio play/pause, flechas salto corto dentro del límite, Home inicio, End último cuadro disponible; no interceptar escritura en otros controles. Slider ARIA min0/max duración/value posición y texto accesible que explique límite disponible. Táctil y200% conservan todas las acciones sin scroll horizontal de página.

Fullscreen aplica al contenedor canvas/controles/ficha, nunca al decoder. Si no hay soporte, usar vista ampliada dentro de página con salida accesible; no abrir fullscreen nativo del video. No ofrecer PiP, velocidad distinta de1x ni controles de reproducción remota en esta iteración. Si el navegador fuerza una presentación del decoder fuera del contenedor, detenerlo antes de continuar; no considerarlo una frontera de seguridad contra herramientas externas.

Sin requestVideoFrameCallback compatible, no activar una versión visible con garantías distintas: mostrar indisponibilidad de reproducción progresiva y conservar resultados/resultado final. La aceptación requiere probar los navegadores objetivo soportados, incluida la recepción de callbacks con decoder no visible.

## Caché y recuperación

LRU de ventanas, máximo16MiB de JSON decodificado estimado y30s acumulados; selección aparte con una sola ficha. Cuatro páginas de anotación en vuelo como máximo, una de estado; cancelar obsoletas. Expulsar anotaciones sin perder cursor/estado del trabajo; retroceder recupera datos del servidor.

snapshot y generation de cada respuesta se validan. Frames partidos se agrupan por frame_index y observation_offset hasta observation_total; no dibujar medias cajas. Vacíos confirmados dibujan el cuadro sin cajas y hacen avanzar cobertura. 409 por snapshot exige releer manifest y reiniciar la ventana, sin POST. Duplicados no agrandan caché ni devuelven selección antigua.

Errores de medio se diagnostican por GET autenticado: 401/403/404/410 retiran; 409 espera; 5xx/red interrumpe recuperación manteniendo solo salida ya validada. Se muestra un estado terminal, no un spinner infinito, si la reproducción no puede recuperarse.

## Gates observables

Con límite42s de120s: permitir10/30 y último frame anterior a42, bloquear60/final por todas las vías expuestas; al crecer a55 conservar la posición. Medir desfase con marcadores de cuadro y captura de salida canvas, incluyendo tareas JS largas, VFR, pausa, saltos, resize y fullscreen. La tolerancia máxima es un intervalo de cuadro; callbacks best-effort por sí solos no acreditan el gate.
