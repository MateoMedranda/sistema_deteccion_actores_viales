# Plan de validación — 009

Estado: protocolo definido antes de implementar. Ningún gate de producto, modelo real o usabilidad queda aprobado por crear estos documentos.

## Línea base y condiciones congeladas

Baseline: 431b6dfccea3fcaccf80feab9039c254604c0718. Extraer una copia de referencia a un directorio de benchmark ignorado, sin cambiar la rama/check-out principal ni crear un worktree. Cada brazo corre en un proceso nuevo con su propio PYTHONPATH, configuración explícita y directorios temporales. No reutilizar SQLite, medios ni .env privados del servicio activo.

Antes de ejecutar, fijar manifiesto privado con hashes de videos/pesos, hardware, CPU/GPU/dispositivo, versiones de Python/Torch/FFmpeg/PyAV/navegadores, umbrales, K, geometría, concurrencia, timeout, TTL, modo de reproducción y digest del manifiesto. Los reportes públicos contienen solo identificadores opacos, hashes no sensibles y agregados, nunca rutas privadas, medios, placas o credenciales.

Tres pares por video, alternando AB y BA de forma equilibrada en el corpus y registrando orden/semilla. Misma máquina sin otras cargas intensivas, calentamiento idéntico y un trabajo activo por brazo. Baseline ejecuta flujo final legacy con enriquecimiento habilitado; candidato, progresivo con enriquecimiento y exportación habilitados. Misma cobertura de cuadros y mismo modelo/tracker. Guardar todos los fallos; no sustituir ejecuciones por otras favorables.

Para clips largos, el arnés puede fijar un timeout idéntico y suficiente antes de medir ambos brazos, sin tocar el .env del usuario. Conservar aparte un caso de timeout300s y otro de fallo inducido tras un commit. La ejecución del usuario (~8,2FPS) es diagnóstico, no baseline certificada.

## Corpus mínimo

| Grupo | Casos | Evidencia esperada |
|---|---|---|
| Cronología | CFR, VFR, B-frames, PTS inicial no nulo/edit list, rotación, último cuadro, archivo<5s | tiempos, duración, geometría y píxeles comparados |
| Identidad | al menos10 tracks, cruces, oclusión, salida, cambio de escena | raw y display por cuadro, sin cajas inventadas |
| Vacío/densidad | sin detecciones, clase no elegible, cuadro con muchas observaciones y páginas partidas | cobertura completa sin confundir vacío con pendiente |
| Progresión | >=30s, un video representativo de~2min, avance más lento/más rápido que reproducción | primera vista, pausas y finalización |
| Evidencia | placa buena tardía, provisional fuera del top-K, errores de localización/OCR/atributos | top-K final y consenso iguales al selector legacy |
| Ciclo de vida | timeout, exportación fallida, crash antes/después de commit, cancel/TTL/race | prefijo correcto o retirada, nunca mezcla de generaciones |

Fixtures deterministas llevan contador visual de cuadro y verdad conocida para demostrar flujo. Videos con modelos reales incluyen referencias de calidad verificadas y permisos de uso; su ausencia deja el gate real pendiente. No usar resultados de 006–008 como sustituto de los de 009.

## Matriz de aceptación

| Criterio | Medición y aceptación |
|---|---|
| SC001 | timestamp de commit del prefijo inicial>=5s hasta primer canvas reproducible: <=2s en todos los videos controlados elegibles; no usar evento previo al commit |
| SC002 | matriz120s/límite42s y controles pointer/touch/keyboard/fullscreen/acciones de media expuestas: 100% bloqueados; captura verifica <=1 intervalo de cuadro posterior tolerado |
| SC003 | 30 saltos por configuración, incluyendo datos expulsados del caché; al menos29 recuperan píxeles/cajas correctos en<1s y el contador de inferencia no aumenta |
| SC004 | >=10 tracks/varios tramos; 100% asociación correcta, commit de resultado→ficha<=2s, sin cambio de posición ni selección |
| SC005 | comparar PTS y marcas visibles en canvas para play/pause/seek/resize/fullscreen; desfase<=un intervalo real del cuadro, no FPS promedio VFR |
| SC006 | contar cuadros únicos admitidos al canvas en ventanas de5s con contenido disponible; >=95% ventanas muestran>=90% de cuadros esperados por PTS a1x. Esperas y saltos se excluyen del denominador de fluidez, pero se reportan completos y su proporción en tiempo de sesión |
| SC007 | análisis/seguimiento/persistencia/publicación medidos por fase; ratio candidato/baseline de tiempo de análisis<=1,10 por video en los tres pares, con enriquecimiento habilitado en ambos. Reportar además exportación, enriquecimiento y tiempo total hasta ambas etapas terminales; no confundir un fallo rápido con una mejora |
| SC008 | fault injection, propietario ajeno, respuesta atrasada y cancelación concurrente: 100% conservación/retirada correcta sin fugas |
| SC009 | cinco participantes reales, al menos4 completan sin ayuda; tres tamaños de pantalla y accesibilidad por teclado/texto200%. Un agente o screenshot no acredita el gate |
| SC010 | muestrear RSS conjunta simultánea cada100ms del árbol API+workers+encoder+gateway, mismo alcance en ambos brazos; peak candidato/baseline<=1,20 por video en tres pares. Reproductor medido aparte; 30 saltos repetidos no superan presupuestos de caché ni presentan crecimiento indefinido |

Para SC007, el intervalo principal empieza al dequeuing del trabajo y termina al confirmar el último cuadro del análisis; incluye decode, detección/tracking, dibujo legacy equivalente, escritura y publicación. Cada brazo mantiene enriquecimiento habilitado desde el punto definido por su flujo. El intervalo extremo a extremo empieza en aceptación y termina con análisis/exportación/enriquecimiento terminales; se reporta con ratios propios y sin ocultar tiempo en cola, aunque el gate principal corresponda al análisis. Registrar exactos los cortes de reloj antes de ejecutar.

## Pruebas de backend y gateway

- Migración additive repetida sobre base antigua/vacía, snapshot consistente, duplicado idéntico/conflictivo, datos fuera de orden y huecos.
- Frames sin vehículos, partición de un cuadro en páginas, tampering de cursor/snapshot y ventanas inválidas; cero válido para from_us/snapshot.
- Atomicidad de archivos/recibos/transacción, crash previo/posterior, retiro durante commit y TTL durante stream.
- Recurso en queued, analyzing, complete, partial_failed y retirado; exportación failed independiente del prefijo válido.
- Reinicio conserva lo publicado sin volver a cero ni reusar un tracker nuevo con la misma generación; legacy recovery permanece.
- GET/HEAD/Range200/206/416, no redirects, budgets y liberación de slots; CSRF requerido en frames/tracks/evidencia/DELETE, excepción nativa solo para source allowlisted.
- Modelo cargado una vez, una evaluación por evidencia/política, máximoK+1; cache final legacy no dispara otra decodificación.
- Fallos de rama no borran otros resultados; fuente cerrada termina todas las unidades antes del TTL o marca fallo explícito.
- Imágenes, plate-preview de imagen, exportación final y conteo por línea siguen pasando sus suites; no reinterpretar processed-cfr.

## Pruebas del reproductor

360x800,768x1024,1440x1000 y texto200%; Chromium, Firefox y WebKit en versiones registradas, con revisión en dispositivos reales para el gate de uso. Evaluar compatibilidad de callbacks del decoder no visible sin depender de display:none. Si un navegador no cumple, informar reproducción no compatible sin mostrar el video crudo; no declarar gate cross-browser aprobado.

Incluir tareas JS largas cerca del watermark: canvas debe congelarse en último cuadro admitido. Evaluar callback ausente/tardía, src que falla, caché expulsado, datos pendientes, tap sobre vehículo, selección vigente y cambio de modo. La interfaz puede inspeccionar todo el original por herramientas de desarrollo del propietario; esto no se cuenta como fuga porque el bloqueo contratado es de presentación.

## Entregables de evidencia

Informe de todos los pares, configuración congelada, resultados por video y gate, trazas/counters no sensibles y protocolo humano. Guardar medios y lecturas sensibles fuera de Git. Crear validation.md/audit.md al implementar con los resultados efectivos y pendientes; no crearlos ahora con resultados supuestos.

Si falla cronología, calidad, frontera, coste o usabilidad, conservar el fallo y abrir trabajo pendiente. Reducir cuadros, seleccionar otro corpus, aumentar umbrales o cambiar el gate después de medir no constituye una corrección.
