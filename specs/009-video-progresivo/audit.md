# Auditoría de entrega — 009

**Resultado: implementación funcional entregada; gates reales y humanos abiertos.** Cierre acotado por la indicación del usuario de diferir la comparación larga. No cambia aceptación ni pendientes de006/007/008.

| Requisitos | Implementación | Evidencia principal |
|---|---|---|
| FR001–003 | TimedVideoDecoder, ProgressiveStore, publicación atómica y revisiones | test_progressive_models/timeline/color/store/lifecycle/race |
| FR004–010 | VideoFrame inmutable, PTS/index verificados, VideoTimeline, intención manual y cachés | progressive, playbackReducer, recovery, mp4Timeline, sourceDecoder, navegación E2E |
| FR011 | Exportación CFR final y detecciones/conteo legacy conservados | suites completas de video/conteo |
| FR012–016 | Evidencia raw top-K, worker compartido, fichas/recortes y progresos independientes | test_progressive_evidence/topk/tracks/workers; trackResults y E2E |
| FR017–020 | Backoff, abort/generation, retiro, owner/CSRF/Range/TTL y recuperación sin reinferencia | lifecycle/security/race/gateway; recovery; sourceRange |
| FR021 | UI compartida, foco, teclado, toque, tamaños y200% | matriz E2E; prueba humana pendiente |
| FR022 | Protocolo y arnés, diagnósticos preservados, paridad de píxeles real | comparación final larga pendiente; sin aceptación de coste |
| FR023 | Sin cambios privados ni modelos; regresión de imágenes/video/conteo |320 backend,118 frontend y build |

Los tipos públicos están en domain/progressive.py; los servicios se separaron en store/media/evidence/enrichment/processing. Varias tareas de pruebas usan archivos consolidados en lugar de uno por historia. La estrategia nativa del diseño se sustituyó con evidencia; plan.md/research.md/contracts/player.md registran la decisión.

Pendientes explícitos: T039 (historial expulsado y memoria prolongada), T074 (completar instrumentación del protocolo con gateway activo), T075 (tres pares reales finales), T076 (medición exhaustiva y plataformas incompatibles) y T077 (cinco participantes). No se declara aceptación completa mientras permanezcan abiertos.

Las métricas públicas contienen solo números agregados de corpus sintético y paridad de píxeles. Los videos autorizados y los ensayos diagnósticos detallados permanecen fuera de Git. La referencia congelada sigue siendo431b6dfccea3fcaccf80feab9039c254604c0718.


## Adenda: cambio aprobado a consulta selectiva y conteo

La nueva instrucción del usuario sustituye el enriquecimiento automático del frontend por selección por Track ID (T093). El modo automático anterior permanece para clientes sin enrichment=on-demand; no se modifica ni se cierra retroactivamente su benchmark pendiente. T094 reutiliza observaciones source-PTS para conteo privado opcional, sin modelos; T095–T096 incorporan ficha de Imagen y editor/contador en el video principal. T097 repara observabilidad, recuperación, finalización y selección de Python; T098 valida con fixtures y T099 actualiza documentación/commit.

Evidencia: test_progressive_demand_count, test_progressive_operational_metrics, test_start_environment, contrato de gateway, progressiveCount/recovery/trackResults y E2E video-progressive-demand. Ver validation.md. Las lecturas y conteos mantienen propiedad, TTL y revocación; no se incorporaron medios privados, secretos ni pesos a la entrega. Las correcciones restantes y gates diferidos continúan abiertos.


Adenda T100–T103: corregida la propiedad del tracker por video y restaurado el editor sobre primer fotograma con arrastre de extremos/segmento. Evidencia: test_tracker_identity, countEditorDrag, E2E selectivo y diagnóstico real de40cuadros documentado en validation.md. Los datos ya analizados con identidades mezcladas requieren nuevo trabajo; no se migran como si fueran correctos.

T104–T106: restaurado el recorte de cajas del tracker antes de persistencia/crops. Causa real, regresiones,335tests y publicación de60cuadros en4lotes documentados en validation.md. Se conserva la validación del store y no se anuncia validación exhaustiva del video completo.


## Seguimiento de cambio aprobado — exportación explícita, 2026-11-24

Se separa la capacidad de analizar de la de producir MP4. Esta enmienda sustituye la obligación anterior de exportar automáticamente en el camino progresivo; los clientes legacy permanecen compatibles. T113–T116 cuentan con pruebas de pipeline, contratos/seguridad/ciclo de vida, frontend y descarga real en dos disposiciones. No se declara aceptación completa de la iteración ni se cierran validaciones largas/humanas pendientes. Véase validation.md y evidence/export-on-demand-validation.json.


## Seguimiento: instrumentación interna y documentación, 2026-11-24

T117–T120 añaden observabilidad sin cambiar el predictor y consolidan trazabilidad documental. El índice docs/registro-evolucion-sistema.md relaciona requisitos, diseño, contratos, tareas, pruebas, sesiones y commits; performance-history.json preserva las comparaciones ordinarias existentes. La evidencia distingue diagnóstico funcional breve, mediciones ordinarias y evaluaciones controladas pendientes. No se declaran optimizaciones del motor ni nuevos FPS por añadir mediciones.

## Seguimiento: política CPU configurable, 2026-11-24

T121–T124 implementados y verificados con 396 pruebas backend y diagnóstico breve real de hilos efectivos, documentados en validation.md y evidence/cpu-thread-check.json. Se usa el callback público on_predict_start para respetar la configuración después de la preparación diferida de YOLO; la instrumentación de tiempos continúa leyendo Results.speed sin hooks de medición. Predictores de vehículos y placas comparten la política de recursos del proceso. Los argumentos del modelo, pesos, entrada, cadencia y conteo no se alteran.

No se acredita una aceleración al pasar de 8 a 16 ni aceptación completa de la iteración. La configuración local conserva 8; el diagnóstico demuestra control efectivo y equivalencia de clases/identidades/cajas enteras únicamente en el tramo medido. Permanecen abiertos los gates largos/humanos y los demás pendientes previos. Referencias e instrucciones preservadas en el índice de documentación del sistema.
