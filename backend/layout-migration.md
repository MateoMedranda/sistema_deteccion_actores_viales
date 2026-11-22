# Reorganización del backend — 2026-11-22

El checkout principal conserva la rama feature/008-exploracion-imagen-video. El código Python, sus pruebas, scripts, pyproject.toml, uv.lock, ejemplos de configuración y archivos .env privados pasan a backend/. Los contratos, especificaciones, herramientas de Speckit y métricas permanecen en la raíz.

La configuración usa rutas ancladas al backend y resuelve specs/ y frontend/ desde la raíz compartida. Se conserva el lock de dependencias y las rutas absolutas de los modelos. El registro de clases compartido y los servidores Playwright apuntan a la nueva ubicación. Playwright admite tanto el entorno existente en .venv como uno nuevo en backend/.venv.

Los entornos Python ya instalados (.venv y el entorno histórico .runtime/ocr-original-env) conservan su ubicación para no invalidar sus ejecutables Windows. La instalación editable existente se actualizó para importar backend/app.

Los originales se conservaron en un respaldo local ignorado dentro de .pytest-tmp-008-preserved/backend-layout/. Las bases SQLite se trasladaron a backend/.runtime y se actualizaron únicamente sus rutas de archivos, conservando propietarios y vencimientos. Los archivos privados no se incorporan al commit.

Las sesiones y los resultados de imagen en memoria se invalidan al reiniciar los servicios. En la comprobación real, un video temporal registrado en la base no tenía disponible su archivo de salida (404); debe volver a analizarse. No se regeneraron resultados ni se cambiaron sus políticas de retención.

Se aislaron las pruebas antiguas que abrían el ciclo de vida de la API con almacenamiento predeterminado, para que no compartan archivos con el servicio en ejecución. Una prueba adicional comprueba que cerrar una API de prueba conserva los archivos de otro servicio. Las imágenes sintéticas del evaluador se generan con Pillow para admitir rutas Unicode de Windows sin depender de la importación previa de modelos reales.

Validaciones:

- 291 pruebas del backend aprobadas; el informe local de pytest se conserva fuera de Git.

- Speckit reconoce specs/008-exploracion-imagen-video con spec, plan y tasks disponibles.
- Los hashes de los archivos previos de .specify/, .agents/, specs/ y metricas/ se conservaron.
- 103 pruebas del frontend aprobadas; compilación TypeScript/Vite aprobada.
- 45 pruebas de navegador de 008 aprobadas en escritorio, tablet y móvil.
- Regresiones anteriores: 111/114 aprobadas inicialmente; tres pruebas de tablet fallaron por esperas de estado o foco. Las tres pasaron en una ejecución posterior aislada, sin modificar sus aserciones ni límites.
- API real /health/live y política autenticada: 200.
- Gateway iniciado mediante backend/start.ps1: sesión 200, cierre 204 y frontend estático 200.
- No se modificaron los contratos API, autenticación, modelos, funcionalidades ni tareas pendientes de las iteraciones anteriores.

Los servicios se reiniciaron durante la migración. Las sesiones y las detecciones de imagen se mantienen en memoria y deben crearse de nuevo. Se conservó la fila de un video temporal previo, pero su archivo no estaba disponible en la comprobación final (404); no se regeneró ni se alteró la política de retención. Para consultarlo es necesario volver a analizar su archivo fuente.
