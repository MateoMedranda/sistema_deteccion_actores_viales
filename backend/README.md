# Backend

Este directorio contiene la API, el gateway privado, las pruebas Python, los scripts de evaluación y sus dependencias.

Desde la raíz del proyecto, abre una terminal para cada servicio:

~~~powershell
./backend/start.ps1 -Service api
~~~

~~~powershell
./backend/start.ps1 -Service gateway
~~~

El script usa primero backend/.venv y, si no existe, reutiliza el entorno .venv de la raíz. No mueve entornos virtuales Windows porque contienen rutas absolutas.

Para una instalación nueva:

~~~powershell
cd backend
uv sync --extra dev
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
~~~

Los archivos privados son backend/.env (API) y backend/.env.web (gateway). Sus ejemplos están junto a ellos. La configuración se carga desde este directorio aunque el proceso arranque desde la raíz.

Los archivos temporales y bases SQLite viven en backend/.runtime. Se conserva sin mover el entorno de diagnóstico histórico .runtime/ocr-original-env en la raíz, igual que .venv/, para no invalidar sus ejecutables instalados. Las rutas relativas de pesos se resuelven desde backend; las rutas que comienzan con specs/ o frontend/ se resuelven desde la raíz compartida. Las rutas absolutas de los modelos se conservan.

Para ejecutar las pruebas con el entorno existente, desde backend:

~~~powershell
../.venv/Scripts/python.exe -m pytest
~~~

Si instalaste un entorno nuevo con uv sync, usa uv run pytest.

Speckit permanece en la raíz: .specify/, .agents/, specs/ y metricas/. Ejecuta allí sus comandos con SPECIFY_FEATURE_DIRECTORY=specs/008-exploracion-imagen-video. Los documentos históricos conservan sus rutas originales; app/, tests/ y scripts/ de esas referencias corresponden ahora a backend/app/, backend/tests/ y backend/scripts/.

Consulta la [guía general](../README.md) para el frontend, los contratos y los flujos de análisis.
