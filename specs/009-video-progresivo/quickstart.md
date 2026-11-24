# Uso y validación — 009

Implementación funcional en feature/009-video-progresivo. La comparación larga se difirió por indicación del usuario; no se declaran aprobados los gates reales de coste ni la prueba humana. Ver validation.md y audit.md.

## Entorno y arranque

Python3.12, FFmpeg/ffprobe y los modelos aprobados existentes. Se añadió av==19.0.2 al backend, mp4box==2.6.0 al frontend y tipos Node22 solo para pruebas. Node debe satisfacer >=20.8.1.

En un entorno nuevo, desde backend:

~~~powershell
uv sync --python 3.12 --extra dev
~~~

Desde la raíz, instalar el frontend con npm --prefix frontend ci. Los secretos continúan únicamente en backend/.env y backend/.env.web. Esta iteración no modifica límites privados ni credenciales.

Tres terminales desde la raíz:

~~~powershell
.\backend\start.ps1 -Service api
~~~

~~~powershell
.\backend\start.ps1 -Service gateway
~~~

~~~powershell
npm --prefix frontend run dev
~~~

Usar el origen exacto de WEB_ORIGIN. Si un servicio ya ocupa su puerto, reutilizarlo o detenerlo desde su terminal; no iniciar duplicados. El script de arranque conserva el entorno compatible existente.

En Video, seleccionar archivo y procesar una vez. La vista aparece durante el análisis al confirmar el buffer inicial. Solo admite navegar por cuadros analizados. Pausar y seleccionar caja/lista abre la ficha y sus recortes; la evidencia representativa indica su instante. Un fallo conserva el prefijo vigente; Limpiar video lo retira.

## Pruebas funcionales aisladas

Desde raíz con el entorno compartido:

~~~powershell
.\.venv\Scripts\python.exe -m pytest backend/tests
npm --prefix frontend test
npm --prefix frontend run build
~~~

Desde frontend:

~~~powershell
npx playwright install chromium firefox webkit
npx playwright test --config playwright.009.config.ts
~~~

La configuración selecciona Python3.12 con av/fastapi, genera clips sintéticos y usa puertos9413/9414/9415 y bases temporales. No necesita videos personales ni el .runtime del servicio. Chromium y Firefox se probaron con reproducción; WebKit Windows valida incompatibilidad sin mostrar el original.

## Comparación real pendiente

El video autorizado fue inspeccionado y se compararon sus3.611 cuadros contra OpenCV: cero diferencias de píxeles tras corregir la conversión. Los ensayos completos anteriores a esa corrección son diagnósticos, no aceptación de la versión final.

Para reanudar el protocolo, usar un directorio privado nuevo en cada ejecución. Desde raíz, sustituyendo la ruta autorizada:

~~~powershell
$evaluationRoot = Join-Path .runtime ("evaluate-009-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
.\.venv\Scripts\python.exe backend/scripts/evaluate_video_progressive.py --video "RUTA_PRIVADA_AUTORIZADA.mp4" --runtime $evaluationRoot --env backend/.env
~~~

El arnés ejecuta tres pares AB/BA, conserva todos los resultados y comprueba el fingerprint de código. No reutilizar una carpeta parcial ni presentar ensayos de otro candidato como resultados finales. Su RSS actual cubre backend/OCR/encoder; completar también medición de gateway activo y reproductor según validation-plan.md.

MAX_VIDEO_DURATION_SECONDS limita duración admitida; VIDEO_JOB_TIMEOUT_SECONDS limita cómputo. El arnés usa su timeout idéntico en ambos brazos sin editar .env. Aumentar duración admitida no acelera el análisis ni equivale a tiempo real.


## Inspección bajo demanda y conteo opcional

Después de actualizar código, detener/reiniciar API y gateway desde sus propias terminales; un gateway antiguo sin --reload seguirá rechazando los parámetros nuevos. Desde la raíz, usar tres terminales:

~~~powershell
.\backend\start.ps1 -Service api
~~~
~~~powershell
.\backend\start.ps1 -Service gateway
~~~
~~~powershell
npm --prefix frontend run dev
~~~

Dentro de frontend, usar `npm run dev` (sin otro --prefix). `backend/start.ps1 -CheckEnvironment` verifica el Python elegido sin iniciar servicios; un primer entorno inválido permite fallback al compatible de la raíz. No es necesario cambiar .env ni aumentar timeout para activar estas funciones. Reiniciar la página renueva la sesión del gateway.

Procesar un video mantiene solo detección/seguimiento automáticos. Pausar y pulsar una caja solicita ese Track ID; la ficha lateral muestra crop original, atributos, placa y su recorte autorizado cuando existe. Volver a seleccionarlo reutiliza la consulta. «Vehículos de este fotograma» despliega la alternativa accesible debajo de los controles, sin lista sobre la ficha.

En «Conteo opcional», el primer fotograma aparece automáticamente. Pulsa y arrastra para dibujar; arrastra los extremos amarillos o el centro para ajustar toda la línea. Las flechas ajustan un extremo enfocado; «Opciones de ajuste» conserva coordenadas precisas y otro fotograma. Activar conteo dibuja la línea en el video principal y muestra cruces arriba a la derecha. Retroceder consulta acumulados históricos; no suma otra vez ni ejecuta detección. Una línea nueva recalcula trayectorias ya disponibles y Desactivar retira el contador. La regla de lado/dirección y un cruce por Track ID conservan el conteo anterior.

La solicitud selectiva fija hasta K recortes disponibles al pedirla; evidencia posterior no vuelve a ejecutar OCR automáticamente. La reducción del número de consultas no acredita por sí sola una tasa de FPS en videos reales. No se ejecuta la comparación larga diferida.


Tras la corrección de identidad, reiniciar la API y crear un análisis nuevo del video. Un trabajo anterior ya contiene asociaciones y recortes por Track ID mezclados; recargar el navegador no repara esos datos históricos. No se borran ni se sobrescriben automáticamente.


## Perfil ordinario por etapas — punto 1 (2026-11-24)

Esta instrumentación observa el camino progresivo existente. No cambia pesos, umbral, entrada del detector, frecuencia de detección, identidad, recortes, conteo ni exportación. No inicia la comparación larga AB/BA pendiente.

### Obtener una medición

1. Desde la terminal de la API, detenerla con Ctrl+C y arrancar el código actualizado. No iniciar una segunda API en el mismo puerto. Desde la raíz del checkout principal:

~~~powershell
cd 'C:\Users\USER\Desktop\Mateo\GESTIÓN DE PROYECTOS'
.\backend\start.ps1 -Service api
~~~

2. Mantener gateway y frontend como de costumbre. En el navegador crear un análisis nuevo del mismo video que resulta lento. Para la primera medición no seleccionar vehículos ni abrir otras inferencias; anotar aparte si el conteo estaba activo. La reproducción puede permanecer abierta tal como se usa normalmente.
3. Esperar a que termine o falle. Se actualiza un resumen aproximadamente cada cinco segundos de trabajo y al finalizar, incluyendo fallos o cancelación durante el procesamiento. No se requiere copiar miles de líneas de consola. Trabajos anteriores a esta actualización no disponen de informe. Si el proceso se cierra abruptamente, puede quedar solamente el último avance con estado `processing`; comprobar `updated_at`.
4. En otra terminal PowerShell, desde la misma raíz, leer el último informe actualizado:

~~~powershell
.\.venv\Scripts\python.exe .\backend\scripts\report_video_profile.py --latest
~~~

El comando imprime la ruta absoluta del JSON. Con la configuración predeterminada se guarda en `backend/.runtime/video-profiles/<job_id>.json`. Un `VIDEO_JOB_DB_PATH` personalizado mueve la carpeta a `video-profiles` junto a esa base de datos; en ese caso pasar `--directory 'CARPETA/video-profiles'` al lector.

Para ver/copiar el JSON completo, válido también en PowerShell 5.1:

~~~powershell
.\.venv\Scripts\python.exe .\backend\scripts\report_video_profile.py --latest --json
~~~

Para conservar el JSON en un archivo fácil de adjuntar en el escritorio:

~~~powershell
.\.venv\Scripts\python.exe .\backend\scripts\report_video_profile.py --latest --json | Set-Content -Encoding UTF8 (Join-Path ([Environment]::GetFolderPath('Desktop')) 'perfil-video.json')
~~~

También se puede seleccionar un informe exacto con `--job ID_DEL_TRABAJO` en lugar de `--latest`. El último es el actualizado más recientemente, no necesariamente uno completado: revisar el ID y el estado mostrados. El lector solo consulta informes; no ejecuta modelos ni inicia pruebas de rendimiento.

### Qué compartir y cómo interpretarlo

Compartir el archivo JSON y, en texto, si se seleccionaron vehículos, si estaba activo el conteo y si había otras aplicaciones/inferencias pesadas. Para observar la contención por enriquecimiento se puede hacer después un segundo análisis del mismo video seleccionando vehículos; no es obligatorio para la primera decisión. Una sola ejecución identifica candidatos a optimización, no acredita los gates comparativos de la iteración.

- `analysis_fps`: cuadros procesados por segundo de tiempo de pared del análisis. Incluye el primer cuadro y sus costes iniciales; excluye la conversión final H.264. No son FPS de reproducción ni una medición aislada de la red neuronal.
- `confirmed_video_seconds_per_wall_second`: segundos de cronología confirmada por segundo de análisis. Un valor menor que 1 indica que, en promedio, el análisis avanza más lento que el video; para continuidad sostenida se necesita margen además del promedio. Es más informativo que comparar FPS nominales cuando la fuente es VFR.
- `analysis_wall_ms`: recorrido de cuadros, espera, recortes, escritura y publicación. `total_wall_ms`: hasta el cierre/limpieza del worker antes del último guardado del informe, incluida conversión final. Excluyen subida, cola previa, carga inicial de modelos y navegador/gateway.
- `stages`: total, llamadas, media y máximo por llamada, coste normalizado por cuadro procesado y porcentaje del análisis. Las llamadas no siempre equivalen a cuadros: tracking incluye su inicialización; publicación procesa lotes; decode también registra el intento final de EOF. `final_encode`, `finalization` y `cleanup` están fuera del análisis y no suman a su porcentaje.
- `detection`: predict con pre/postprocesamiento y transferencia de las cajas a CPU; la clase básica se obtiene en esa misma predicción. `tracking`: asociación ByteTrack y conversión/recorte de cajas, sin ejecutar YOLO. Si se usa un adaptador externo sin interfaz de perfil, se informa explícitamente `detection_tracking_combined`, sin inventar una separación.
- `resource_wait`: espera para adquirir exclusivamente el bloqueo compartido de detección/enriquecimiento. No es tiempo de YOLO ni identifica por sí solo al responsable de toda contención. Las esperas de SQLite permanecen en publicación o controles según dónde ocurran.
- `evidence`: selección, compresión PNG y escritura de candidatos originales. No significa que se esté ejecutando OCR automáticamente. `annotation` y `video_write` permiten cuantificar por separado el dibujo y la escritura actuales del MP4 anotado.
- `publication`: transacción de resultados/evidencias y actualización de progreso; `controls`: comprobaciones de estado/retirada/timeout. `frame_logging` incluye la consulta RSS y el log existente por cuadro; no mide toda la actividad de logs de la aplicación.
- `other_analysis_ms`: trabajo no desglosado, contexto inicial y coste de instrumentación fuera de bloques. No se fuerza el reparto para aparentar que todo pertenece a YOLO. Los tiempos miden pared y planificación del sistema, no porcentaje de utilización de CPU.
- `first_publication_ms`: primer lote confirmado desde el inicio del worker; `initial_buffer_available_ms`: momento en que alcanza el umbral de buffer configurado. Puede ser nulo en clips cortos; ninguno acredita el primer cuadro visto por el usuario.

Los informes contienen solo agregados y contexto mínimo (modelo por nombre, dispositivo, umbral, versiones, dimensiones/FPS), sin imágenes, matrículas, resultados por vehículo, nombres/rutas de la carga, API keys ni credenciales. Son diagnósticos locales, no se exponen por API y permanecen disponibles tras la expiración de medios hasta su eliminación manual. La carpeta es ignorada por Git. Cada trabajo mantiene un JSON de tamaño acotado, actualizado mediante sustitución atómica, sin listas de muestras por cuadro. El coste de guardar avances se contabiliza en `profile_reporting`; un error de escritura se registra sin propagarlo al análisis.
