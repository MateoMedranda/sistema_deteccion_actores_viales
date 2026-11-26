# Validación técnica011 —2026-11-25

Entrega técnica completada;74/75 tareas marcadas. Pendiente externo: T071/SC-009, prueba de uso con cinco personas. Ver `human-validation.md`.

- Backend: suite completa556pruebas aprobadas; después se añadió un caso de fecha con zona y pasó el grupo contractual30/30.
- Frontend: suite completa191pruebas/72archivos aprobados; después pasó el grupo2/2 de cancelación aislada con un caso adicional.
- TypeScript/Vite: build aprobado. Permanece advertencia de chunk minificado>500kB; no bloquea el build. Backend conserva aviso de deprecación de anyio.
- Navegador Chromium:21combinaciones de escenario/tamaño verificadas en varias pasadas, más una medición de velocidad. Las tres pruebas finales de espera pasaron al consultar el prefijo real del backend; seis revalidaciones de layout/nombres60grafemas/latencia pasaron. La prueba temporal no se repitió en tablet/móvil.
- Reproducción de30s:0,5×=59,979s,1×=30,099s,2×=15,020s; dentro±5%. No son FPS de detección.
- Ensayo de rendimiento0/1/10líneas: objetivos de lock/GET/catch-up cumplidos. Ver informe y límites en `evidence/performance-review.md`. No se ejecutó comparación larga con modelos reales.

## Fallos encontrados y corregidos

Contrato pending/total, parser de objetos individuales, reconciliación al recargar bajo StrictMode, borrador inicial frente a configuración ya confirmada, mensaje al rechazar colores repetidos, visibilidad de espera sin ancla, espacio reservado en fullscreen y cancelación de un borrador sin descartar el de otra línea. La fecha de vencimiento exige zona horaria.

Los ensayos también corrigieron expectativas: uno de seis objetos cruza la prolongación, fuera del segmento; debe excluirse (5cruces). El prefijo del backend sigue avanzando mientras el canvas está pausado; su atributo solo cambia al repintar y no es un medidor vivo del backend.

## Operación y límites

Reiniciar API y gateway tras instalar `regex` con el Python3.12 existente. El frontend ofrece velocidades0,25×–2× y10líneas activas por defecto, nombres y colores únicos. Conteos exactos por tiempo fuente, identidad local y línea; no sumar tarjetas para obtener vehículos físicos únicos. Cambiar geometría reconstruye solo esa línea; metadata conserva eventos. El inventario global y la exportación siguen independientes.

Recarga: se conserva solo ID opaco y expiración en sessionStorage; backend autoriza y conserva configuración/cruces hasta el TTL original. Nuevo archivo, limpieza o reinicio de sesión descartan referencia y borradores. Una capacidad404 conserva el video; autenticación/vencimiento mantienen la autoridad existente. No se exponen claves al navegador.

Las pruebas usan servicios temporales9413/9414/9415 y no detienen procesos del usuario. La limpieza deliberada puede generar logs ApiError en el worker sintético al retirar un trabajo en marcha. Es un efecto del fixture, no un fallo de las verificaciones finales.
