# Revisión del comparador sintético011

Fixture300cuadros×20observaciones, un calentamiento y cinco muestras por caso. Referencia previa de escritura única; ni modelos reales ni videos privados. Valores de las medianas, en ms salvo RSS en MiB.

| Caso | Publicar/reducir | Publicación | Catch-up restante | p95 lock | p95 GET | RSS proceso |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0-steady | 116.259 | 108.515 | 0.000 | 0.000 | 0.138 | 50.090 |
| 0-catchup | 111.848 | 105.139 | 0.000 | 0.000 | 0.331 | 50.141 |
| 1-steady | 264.856 | 128.821 | 0.224 | 6.225 | 0.381 | 50.496 |
| 1-catchup | 113.639 | 106.064 | 84.751 | 4.575 | 0.415 | 50.492 |
| 10-steady | 398.526 | 112.797 | 0.224 | 8.566 | 1.203 | 50.871 |
| 10-catchup | 114.547 | 107.455 | 264.350 | 8.138 | 1.020 | 50.926 |

Objetivos: p95lock≤10ms, GET≤250ms y catch-up de10líneas≤5000ms: {'lock_p95_pass': True, 'get_pass': True, 'catchup_pass': True}. El lock incluye commit SQLite; los pasos liberan el recurso antes del siguiente lote. Los límites son20cuadros/200pares/2MiB y presupuesto cooperativo5ms entre cuadros, no un plazo duro por operación del sistema.

Caso0líneas frente a la referencia: análisis -2.46%, publicación -3.17%. No se activó la investigación de degradación>5%; una diferencia favorable de este ensayo breve no demuestra aceleración de YOLO. No se sustituyó la referencia ni se ejecutó la comparación larga.

Catch-up medido con turnos consecutivos: excluye las esperas de50ms del worker. RSS es del proceso Python completo, no memoria exclusiva de una línea. Los tiempos incluyen sistema operativo y varían por equipo. `source_sha256` identifica el backend medido, `baseline_source_sha256` la referencia anterior. El reporte conserva muestras individuales y lag final.
