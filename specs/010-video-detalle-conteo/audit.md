# Auditoría de implementación 010 — 2026-11-24

Implementada en checkout principal, rama feature/010-video-detalle-conteo. Se conservan cambios existentes y los45 CSV históricos no versionados; no se añaden al commit. Los checklists se trataron como puerta de solo lectura: requirements.md16/16.

| Capacidad | Tareas | Evidencia |
|---|---|---|
| Referencia previa, fixtures y contratos comunes | T001–T008 | publication-baseline.json; pruebas foundation |
| Ficha compartida sin scroll completo | T009–T015 | ui-layout.json; regresión de imagen y capturas |
| Consulta exacta inmutable bajo demanda | T016–T033 | inspection-validation.json; watchdog, permisos y TTL |
| Segmento dirigido e histórico por clase elegible | T034–T047 | directed-count-validation.json; CAS, navegación y toque |
| Inventario final independiente por clase | T048–T058 | inventory-validation.json; votos/publicación/backfill |
| Exportación etiquetada explícita | T059–T068 | label-export-validation.json; cuadro MP4 revisado |
| Recursos, integración, rendimiento y documentos | T069–T074 | test-summary.json, publication-overhead.json, publication-paired-check.json; validation.md |

Los24 FR y9 SC conservan cobertura en task-generation.md; todas las74 tareas tienen comprobación o entrega documental. Las pruebas son controladas:446 pytest,142 Vitest,18 casos de navegador más2 táctiles y2 repeticiones finales; build aprobado. Estos resultados no constituyen una evaluación de precisión con vehículos reales.

## Decisiones y resultados

La ficha comparte contenedor semántico y estilos; los adaptadores conservan datos/evidencia propios de cada origen. La selección captura el índice realmente pintado, no FPS nominales. La extracción usa el PTS racional persistido y la conversión aprobada en un hijo acotado; no cambia detector ni reutiliza una aparición antigua. El crop y sus IDs permanecen inmutables; resultados/cachés/derivados respetan TTL y aislamiento.

El contador usa centros medidos, segmento finito y dirección explícita. El evento congela la clase elegible al confirmarse y no cambia por OCR/votos futuros. El inventario consolida identidades independientemente de línea y selección; personas quedan excluidas y categorías desconocidas requieren revisión. Exportar usa un renderer/caché privados opt-in y el mismo worker existente; omitir renderer conserva la interfaz anterior.

T071 investigó el exceso del microbenchmark: +31.47% frente a la referencia histórica y +8.96% en el contraste breve AB/BA (0.0308ms/cuadro adicionales). No se elimina el informe desfavorable ni se interpreta como el rendimiento de YOLO. Ver límites y comandos en validation.md. No se abre la comparación larga aplazada.

## Historial confirmado

- 1b96477: referencia previa y presentación común.
- 2957870: inspecciones por fotograma bajo demanda.
- c96c7fb: preservación UTF-8 en regresiones de inspección.
- c0604c4: conteo dirigido finito e histórico.
- 11a7c5b: inventario independiente por clase.
- 1d0bcb4: exportación etiquetada y ciclo de vida privado.
- El commit de cierre incorpora esta auditoría, informes y tareas terminadas; consultar git log para su identificador final. Las métricas metodológicas se cierran después de confirmar el trabajo.

## Límites conservados

No se cambian modelo/pesos, hilos, cadencia, configuración privada ni contratos legacy. Identidades fragmentadas pueden representar el mismo vehículo físico. Sin evidencia/PTS/procedencia suficiente se declara indisponible y se requiere nuevo análisis. El MP4 conserva el comportamiento de exportación existente, sin prometer precisión VFR adicional. Comparación larga, calidad real exhaustiva y pruebas humanas de009 siguen pendientes; no bloquean las capacidades controladas autorizadas de010 ni se marcan aprobadas.
