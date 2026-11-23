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
