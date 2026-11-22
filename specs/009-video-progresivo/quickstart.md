# Quickstart de validación — 009

**Estado**: diseño; las rutas, módulos y pruebas de 009 todavía deben implementarse. [Contratos](contracts/README.md), [modelo de datos](data-model.md), [protocolo de medición](validation-plan.md). Esta guía no acredita gates.

## Preparación

Trabajar en checkout principal y rama feature/009-video-progresivo, conservando cambios previos. Python3.12, entorno compatible existente y frontend/node_modules; FFmpeg/ffprobe y modelos aprobados para pruebas reales. Secretos únicamente en backend/.env y backend/.env.web.

No copiar .env a una carpeta versionada, no reinstalar Python3.15 y no ejecutar benchmark/tests contra .runtime del usuario. Durante implementación se añadirá av==19.0.2 al lock y se instalará de forma controlada; este plan no cambia dependencias.

Si se prepara un entorno nuevo, desde backend:

~~~powershell
uv sync --python 3.12 --extra dev
~~~

## Arranque actual

Desde la raíz del checkout, en tres terminales:

~~~powershell
.\backend\start.ps1 -Service api
~~~

~~~powershell
.\backend\start.ps1 -Service gateway
~~~

~~~powershell
npm --prefix frontend run dev
~~~

Abrir el origen exacto configurado en WEB_ORIGIN; para Vite predeterminado suele ser http://localhost:5173. El proxy usa gateway4174 y API8000. Si ya están encendidos no iniciar otra copia en el mismo puerto. Los scripts eligen un Python compatible instalado; la API key no se introduce en el navegador.

MAX_VIDEO_DURATION_SECONDS controla duración de entrada; VIDEO_JOB_TIMEOUT_SECONDS controla tiempo de procesamiento. Esta etapa no modifica ninguno. El arnés establece límites propios idénticos para ambas versiones sin editar configuración privada.

## Checks actuales y futuros

Desde raíz, con el entorno compartido existente:

~~~powershell
.\.venv\Scripts\python.exe -B -m pytest -c backend/pyproject.toml backend/tests -p no:cacheprovider
npm --prefix frontend run test
npm --prefix frontend run build
~~~

Si se utiliza backend/.venv instalado con Python3.12, sustituir únicamente el ejecutable por backend/.venv/Scripts/python.exe. Los nuevos tests deben aislar todos los stores y no arrancar pesos reales para comprobar contratos.

Los servidores de pruebas Playwright4173/4174/8767 no deben colisionar con el gateway personal. Al implementar, configurar puertos de test alternativos o ejecutar en un entorno aislado, sin matar procesos del usuario. Desde frontend, en ese entorno:

~~~powershell
npx playwright test --config playwright.config.ts
npx playwright test --config playwright.008.config.ts
npx playwright test video-progressive --project desktop
~~~

El último comando y los casos009 solo serán ejecutables después de crear sus pruebas. El protocolo incluye tablet/móvil, Firefox/WebKit y texto200%; los proyectos necesarios se añaden en tasks sin quitar regresiones existentes.

## Escenarios que debe demostrar la implementación

1. Subir video>=30s en modo progresivo. Antes de finalizar todo el trabajo, confirmar5s iniciales y habilitar reproducción en<=2s desde su disponibilidad.
2. Con fuente120s y límite42s, reproducir18, ir a10/30, volver al último cuadro anterior a42 e intentar60/final: solo los intentos válidos cambian la salida.
3. Al pasar el límite42→55, conservar posición. Llegar al límite pausa por espera; datos nuevos reanudan intención play. Una pausa manual permanece.
4. Con tail terminal<5s y video corto<5s, reproducir todo el tramo disponible sin esperar un margen imposible.
5. Pausar, seleccionar caja o lista y recibir enriquecimiento progresivo por el mismo Track ID; verificar evidencia con instante y provisional/final, sin re-inferencia por navegar.
6. Provocar timeout después de un commit: prefijo sigue consultable hasta su TTL como parcial. Provocar exportación fallida: análisis completo sigue reproducible. Cancelación/retirada/vencimiento eliminan acceso y respuestas tardías no lo restauran.
7. Revisar VFR, cuadros vacíos, rotación, fullscreen y una tarea JS larga cerca del límite; ningún cuadro futuro se presenta por mostrar el decoder crudo.
8. Repetir30 saltos con caché expulsado y consultar snapshot viejo: recuperación acotada, sin crecimiento indefinido ni mezcla de páginas.

La prueba source Range del contrato necesita autenticación administrada; los clientes directos existentes siguen usando su API key de forma privada. No guardar comandos que contengan secretos en documentación o trazas.

## Benchmark y cierre

Se implementará backend/scripts/evaluate_video_progressive.py con opciones --manifest, --baseline-ref, --output y --real-models. Es una interfaz prevista del arnés, no un script ya disponible. Su manifiesto congela corpus/condiciones antes de ejecutar y genera métricas sin medios/placas/rutas privadas.

Aplicar exactamente [validation-plan.md](validation-plan.md): tres paresAB/BA por video, same hardware/modelos, enriquecimiento habilitado, tiempo análisis<=110% y RSS<=120%. Reportar pausas, tiempo extremo a extremo y memoria del reproductor por separado. Fixtures sintéticos no acreditan coste/precisión reales ni prueba humana de cinco personas.

Tras implementar, ejecutar analyze/converge y registrar resultados efectivos. Los pendientes de 006,007,008 permanecen independientes. El siguiente paso de este plan es generar tasks.md, no implementar directamente ni declarar aceptación.
