# Revisión del comparador sintético011

Fixture300cuadros×20observaciones, un calentamiento y cinco muestras por caso. Referencia previa de escritura única; ni modelos reales ni videos privados. Valores de las medianas, en ms salvo RSS en MiB.

| Caso | Publicar/reducir | Publicación | Catch-up restante | p95 lock | p95 GET | RSS proceso |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0-steady | 111.31 | 103.63 | 0.00 | 0.00 | 0.21 | 50.62 |
| 0-catchup | 127.45 | 120.02 | 0.00 | 0.00 | 0.25 | 50.71 |
| 1-steady | 243.26 | 126.62 | 0.14 | 4.86 | 0.40 | 51.17 |
| 1-catchup | 132.34 | 123.74 | 86.05 | 4.67 | 0.35 | 51.13 |
| 10-steady | 414.74 | 123.25 | 0.11 | 8.40 | 0.98 | 51.36 |
| 10-catchup | 136.96 | 128.55 | 257.91 | 8.16 | 1.05 | 51.41 |

Objetivos: p95lock≤10ms, GET≤250ms y catch-up de10líneas≤5000ms: {'lock_p95_pass': True, 'get_pass': True, 'catchup_pass': True}. El lock incluye commit SQLite; los pasos liberan el recurso antes del siguiente lote. Los límites son20cuadros/200pares/2MiB y presupuesto cooperativo5ms entre cuadros, no un plazo duro por operación del sistema.

Caso0líneas frente a la referencia: análisis -6.61%, publicación -7.53%. No se activó la investigación de degradación>5%; una diferencia favorable de este ensayo breve no demuestra aceleración de YOLO. No se sustituyó la referencia ni se ejecutó la comparación larga.

Catch-up medido con turnos consecutivos: excluye las esperas de50ms del worker. RSS es del proceso Python completo, no memoria exclusiva de una línea. Los tiempos incluyen sistema operativo y varían por equipo. `source_sha256` identifica el backend medido, `baseline_source_sha256` la referencia anterior. El reporte conserva muestras individuales y lag final.
