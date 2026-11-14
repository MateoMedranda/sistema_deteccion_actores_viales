# Métricas de la primera iteración

**Proyecto:** Sistema de detección de actores viales  
**Funcionalidad:** `001-deteccion-imagen-vial`  
**Fecha de corte:** 22 de octubre de 2026  
**Fuente:** extensión `speckit-metricas` (versión 0.3.0).

## Tamaño y avance

| Medida | Valor |
|---|---:|
| Historias de usuario | 3 |
| Requisitos funcionales | 10 |
| Criterios de éxito | 5 |
| Escenarios de aceptación | 6 |
| Tareas planificadas | 54 |
| Tareas completadas | 46 (85,2 %) |
| Tareas pendientes | 8 (14,8 %) |
| Puntos de tarea (PTS) | 214 |
| Puntos agregados o eliminados | 0 / 0 |

Los **214 PTS** son una medida de tamaño y complejidad obtenida al clasificar manualmente las tareas de `tasks.md` por tipo y complejidad. No equivalen por sí solos a horas: permiten comparar futuras iteraciones y, cuando exista historial suficiente, estimar el esfuerzo.

## Esfuerzo, calendario y código

| Medida | Valor |
|---|---:|
| Esfuerzo humano estimado | 6,25 h (rango orientativo: 5,5 a 7,0 h) |
| Esfuerzo del agente estimado | 6,25 h de asistencia; no se suma al esfuerzo humano |
| Calendario observado en Git | 1 día |
| Commits observados | 1 |
| Código entregado | 841 líneas |
| Pruebas agregadas | 495 líneas |
| Código eliminado | 0 líneas |
| Desperdicio declarado | 0 líneas (0 %) |
| Costo humano estimado | USD 18,75 (tarifa académica supuesta: USD 3,00/h) |
| Modelo de IA | Codex, asistente basado en GPT-5; versión exacta no capturada |

> **Estimación, no registro automático:** la extensión fue inicializada después de que ya se había realizado parte del trabajo. La estimación de 6,25 h se obtuvo con 214 PTS y una productividad de referencia de 34,9 PTS/h (96 PTS en 2,75 h, ejemplo académico suministrado). La misma cifra se muestra para la asistencia de IA como duración aproximada de colaboración, pero no debe sumarse al esfuerzo humano: ambos ocurrieron en la misma ventana de trabajo. El costo es una simulación con USD 3,00/h; puede reemplazarse por la tarifa institucional o personal aplicable.

### Distribución estimada por fase

| Fase | Horas estimadas |
|---|---:|
| Constitución | 0,50 h |
| Especificación | 0,50 h |
| Planificación | 0,75 h |
| Tareas | 0,50 h |
| Implementación y pruebas iniciales | 2,75 h |
| Convergencia, auditoría y cobertura | 1,00 h |
| Métricas | 0,25 h |
| **Total estimado** | **6,25 h** |

Los valores cero de los resúmenes automáticos no significan que el esfuerzo fue cero; indican que no existen sesiones cerradas con horas registradas. Tampoco se debe interpretar el 0 % de desperdicio como ausencia absoluta de retrabajo, pues solo se mide desde commits y sesiones registrados.

## Evidencia de calidad disponible

- La auditoría de la iteración reporta 8 pruebas verificadas con éxito y 29 pruebas recolectadas.
- La cobertura observada para el subconjunto ejecutado fue 66 %; no representa todavía cobertura integral del sistema.
- Quedan pendientes 8 tareas, entre ellas la ejecución completa de las pruebas por historias, la captura persistente de métricas de latencia y el cierre de evidencia de requisitos.

## Cómo medir el esfuerzo desde ahora

Antes de comenzar una fase, abre una sesión. Reemplaza los valores entre ángulos por el identificador exacto que muestra tu herramienta de IA; no uses valores inventados.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .specify\extensions\metricas\scripts\powershell\sesion.ps1 iniciar `
  -Funcionalidad "001-deteccion-imagen-vial" `
  -Fase implementar `
  -Herramienta codex `
  -ModeloIA "<modelo-exacto>" `
  -NivelRazonamiento "<nivel-exacto>"
```

Al terminar y después de confirmar los cambios en Git, cierra la sesión:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .specify\extensions\metricas\scripts\powershell\sesion.ps1 cerrar `
  -Actividad "Implementación y verificación de la iteración" `
  -Horas <horas-reales>
```

Después actualiza los resúmenes:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .specify\extensions\metricas\scripts\powershell\recolectar.ps1
```

Los archivos generados quedan en `metricas/salidas/resumen-proyecto.csv` y `metricas/salidas/resumen-funcionalidades.csv`.
