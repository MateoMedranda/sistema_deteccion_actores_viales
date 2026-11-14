# Guía de validación local: Interfaz web prototipo vial

## Prerrequisitos

- Python 3.12, uv, pesos/configuración válidos y FFmpeg/ffprobe para el backend.
- Node.js LTS y npm para el frontend.
- Una API key configurada solo en el .env privado del backend.
- En desarrollo, permitir el origen de Vite en la configuración CORS del backend.

## Inicio

1. En la raíz del repositorio, sincronice el backend: uv sync --extra dev.
2. Copie .env.example a .env, configure las rutas privadas de modelos y API key, y permita http://127.0.0.1:5173 y/o http://localhost:5173 en la lista CORS.
3. Inicie la API: uv run uvicorn app.main:app --reload.
4. En otra terminal: cd frontend, npm install y npm run dev.
5. Abra la URL que Vite muestra, confirme la URL del backend y escriba la API key solo para esta sesión de navegación.

## Escenarios de validación

### Imagen

1. Cargue una imagen permitida y analícela.
2. Confirme progreso, detecciones e imagen anotada.
3. Repita con archivo inválido; debe aparecer un error claro sin secreto, ruta o respuesta técnica.

### Video y conteo

1. Cargue un único video permitido y espere completed.
2. Confirme estado, progreso, resumen, detecciones paginadas y video anotado.
3. Dibuje y ajuste una línea; redimensione la ventana y confirme que los extremos conservan su posición proporcional.
4. Inicie conteo y compruebe estado, eventos y totales por clase/sentido.

### Enriquecimiento y limpieza

1. Sobre una fuente vigente, solicite enriquecimiento y espere resultado.
2. Compruebe atributos y estados de placa. El texto solo puede aparecer si el backend reporta read.
3. Pulse reiniciar: la interfaz intenta cancelar trabajos activos y elimina archivos, IDs, resultados, URLs de objeto y texto de placa de la vista.

## Pruebas

- Frontend: desde frontend/, ejecutar npm run test y npm run test:e2e.
- Backend: desde la raíz, ejecutar uv run pytest tests/contract/test_count_jobs_contract.py tests/integration/test_count_job_routes.py tests/integration/test_cors.py.
- La suite completa existente continúa con uv run pytest.

Consulte [frontend-backend.md](contracts/frontend-backend.md) para contratos y [data-model.md](data-model.md) para el ciclo de estado y manejo de datos sensibles.

