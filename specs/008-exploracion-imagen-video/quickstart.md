# Quickstart de validación —008

**Estado**: funciones implementadas; resultados efectivos en validation.md y audit.md. Los gates pendientes no equivalen a aceptación integral.

## Requisitos

Checkout principal en feature/008-exploracion-imagen-video, Python3.12/.venv y frontend/node_modules existentes, FFmpeg/ffprobe disponibles y modelos/credenciales privados ya aprobados. Conservar configuración y archivos previos. No usar VITE_* para la API key. [Gateway](contracts/gateway.md) fija la frontera local/privada.

## Arranque

Desde raíz, terminal del backend:
~~~powershell
.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
~~~

Configurar .env.web privado a partir de .env.web.example. Variables: WEB_BACKEND_URL=http://127.0.0.1:8000, WEB_BACKEND_API_KEY con el secreto aprobado editado localmente, WEB_ORIGIN=http://127.0.0.1:4173. Nunca pegar el secreto en comandos guardados, commits, capturas o documentación.

Producción local:
~~~powershell
npm --prefix frontend run build
.venv/Scripts/python.exe -m uvicorn app.web.main:app --host 127.0.0.1 --port 4173
~~~

Desarrollo: mismo WEB_ORIGIN4173, gateway en4174 y Vite en4173 con proxy de /web y /web-api hacia4174 preservando Host/Origin:
~~~powershell
.venv/Scripts/python.exe -m uvicorn app.web.main:app --host 127.0.0.1 --port 4174
npm --prefix frontend run dev -- --host 127.0.0.1 --port 4173 --strictPort
~~~

La web se abre en127.0.0.1:4173 y no pide URL/key. Los accesos remotos requieren HTTPS/ingreso privado autenticado existente; no exponer ninguno de estos puertos al público como fallback.

## Recorridos

1. Sesión: configuración válida, ausente/inválida, key rechazada y upstream no disponible. Revisar mensajes seguros y ausencia del canario en datos del navegador.
2. Modos: iniciar trabajo, pasar Imagen/Video y volver. Estado/TTL continúan; Video pausa al ocultarse sin cancelar procesamiento.
3. Imagen:10 escenas/3densas, Ajustar/100/200/400%, pan/teclado/toque, selección correcta, sin números ni otro análisis. Fuera del viewport la página se desplaza normalmente.
4. Video: analizar una sola vez; observar queued/frames/encoding/publishing/ready y enriquecimiento automático. Reproducir/buscar por Range sin esperar lectura. Cero elegibles=no aplicable.
5. Fichas: todas las páginas/track IDs, atributos/placa/estados y referencia al video procesado; no confundir evidencia con currentTime.
6. Recuperación: recibo perdido reutiliza intención; fallo conocido reintenta solo la fase válida; cancelar/reset/TTL no restaura evidencia.
7. Conteo: misma fuente/linea, datos raw y artefacto003 conservados. No se implementan clicks de contornos de video en008.

## Comandos de pruebas

Suites de regresión:
~~~powershell
.venv/Scripts/python.exe -B -m pytest -o addopts='' -q
npm --prefix frontend run test
npm --prefix frontend run build
# Desde frontend:
./node_modules/.bin/playwright.cmd test
./node_modules/.bin/playwright.cmd test --config=playwright.008.config.ts
~~~

Fixtures controlados y evaluador:
~~~powershell
.venv/Scripts/python.exe tests/e2e/build_video_presentation_fixtures.py
.venv/Scripts/python.exe scripts/evaluate_video_presentation.py --manifest frontend/e2e/fixtures/video-presentation/manifest.json --output specs/008-exploracion-imagen-video/video-presentation-summary.json
~~~

El generador crea solo fixtures sintéticos en carpeta008 propia, sin reemplazar fixtures anteriores. El evaluador sigue [validation-protocol.md](validation-protocol.md), conservará todos los resultados y no publica medios.

## Resultado esperado y límites

Contratos/privacidad/lifecycle verificados; UI360/768/1440 y200%; zoom<=1px y p95<=200ms; video limpio con gates de fluidez/IoU/lag y tiempo/RSS<=110% baseline. Medidas que aún no se ejecuten se declaran pendientes. Fallar un gate impide cierre integral, no habilita modificar métricas o modelos.

Cada incremento confirma solo sus archivos pertinentes en un commit. Revisar auditoría y ejecutar converge antes de declarar aceptación integral. No se cierran006/T067–T068 ni007/T061–T064/T070.

--benchmark mide solo presentación sobre raw sintético. --real-model-benchmark añade3 pares AB/BA con detector/tracker y pesos locales, encoder y publicación; conserva fallos. Enriquecimiento y RSS del gateway se reportan por separado. No iniciar ambos arneses Playwright juntos: usan4173/4174/8767.
