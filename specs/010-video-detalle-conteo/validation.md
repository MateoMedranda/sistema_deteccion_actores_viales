# Validación de implementación 010

Rama feature/010-video-detalle-conteo. Implementación en curso; solo se marcan tareas con evidencia. No se ejecuta la comparación larga ni se cierran gates humanos anteriores.

## T001 — referencia previa

Antes de modificar backend/app o frontend/src: desde backend, `../.venv/Scripts/python.exe tests/performance/test_video_detail_overhead.py capture`. Un calentamiento y cinco muestras sintéticas; referencia de escritura única con entorno, fixture y huella fuente. Comparación final usa `compare`, nunca recaptura una base del candidato. No mide FPS del detector real.

## T001–T015: bases y ficha compartida. Pytest inicial: 3 pruebas aprobadas; Vitest de shell, imagen y reproducción; build aprobado. Playwright layout010: 3 proyectos (desktop/tablet/mobile), cada uno comprueba 360/768/1440 y guarda capturas sintéticas en frontend/test-results/010-artifacts. No se interpreta este checkpoint como inspección temporal implementada.

## T016–T033: inspección temporal. Pruebas backend de PTS exacto, watchdog, contextos, contratos, vencimiento/tombstones y retirada aprobadas; Vitest: 3 regresiones de selección/cache/assets. Build aprobado. E2E desktop con video sintético verifica frame_index del canvas, recorte del instante, enriquecimiento y 30 segundos de URL estable; seek cierra ficha. Contratos de respuesta tipados, DTO de preview propio, TTL/cuotas configurables. Sin detección de escena al inspeccionar.

## T034–T047: conteo dirigido. Geometría finita, clases elegibles inmutables, CAS/revisión, cobertura exclusiva y GET sin efectos validados; regresiones de identidad/conteo legacy aprobadas. Vitest flecha perpendicular en píxeles fuente y build aprobados. E2E desktop: primer fotograma antes de POST, borrador aplicado sin segunda carga, cinco idas/vueltas (0/5 estables), inversión aplicada a nueva revisión (0). El primer ensayo excluyó correctamente un vehículo fuera del extremo; se amplió el segmento del fixture para incluir las cinco trayectorias de referencia.
