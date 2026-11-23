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
