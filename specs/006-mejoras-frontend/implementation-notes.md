# Decisiones concretas de implementación

- El estado visual se expresa con Phase y enrichmentStage: detectar, enviar, en cola, procesar y los estados terminales se distinguen sin poner controladores o temporizadores en el reducer. La presencia de response permite conservar la detección ante fallo de enriquecimiento.
- El visor usa la proporción natural del elemento img y porcentajes sobre su área real. No hay un contenedor de altura fija con contain que introduzca bandas; por ello no se estima letterboxing ni se amplían hitboxes. La lista ofrece controles equivalentes cuando una caja es pequeña o queda detrás de otra.
- La extracción de placa revierte exclusivamente el error de representación de coordenadas enteras normalizadas con tolerancia de Number.EPSILON. No interpola, mejora ni reconstruye contenido.
- Se reutilizan las dependencias existentes. Prettier 3.6.2 se ejecutó como herramienta temporal para facilitar revisión, sin añadir dependencias ni modificar el lockfile.
- Todos los stores del servidor de pruebas están bajo TemporaryDirectory, incluidos enriquecimiento y fuentes. tests/unit/test_frontend_test_isolation.py evita volver a utilizar rutas de runtime de desarrollo.
- Los puertos 4173/8767 son de pruebas; no se detuvieron servidores personales de 5173/8000 ni se cambiaron configuraciones privadas.
- El cierre abrupto del navegador no garantiza cancelación remota. Reset y cambio de identidad limpian la UI inmediatamente e intentan cancelar con el cliente anterior; TTL y el janitor limitan la evidencia en el servidor.
- No se cambian pesos, modelo, umbrales, autenticación ni especificaciones históricas. Los contratos nuevos son aditivos y se validan tanto en OpenAPI documentado como generado.


## Correcciones de convergencia

Cada medio tiene estado y recuperación independientes. La identidad fuente/intento vive en la operación y no depende del momento de render de React. Los métodos legacy admiten señales opcionales para abortar sin imponer los plazos de imagen al video. La línea se invalida en padre e hijo al borrar o cambiar la fuente. Los recibos de propiedad/vencimiento son privados, mínimos y no contienen media ni datos OCR; permiten purga de archivos gestionados tras reiniciar sin asumir propiedad de archivos históricos desconocidos. Ver convergence-validation.md.

## Retorno interno de finalización — T083

finish devuelve el estado de la decisión tomada bajo el bloqueo/transacción de publicación. El worker lo asigna a la métrica del trabajo, sin una lectura posterior que podría observar otra limpieza/TTL. La expiración sigue representándose por eliminación y 410, sin añadir estados persistidos ni cambiar contratos HTTP. Unidades/ramas ya inferidas conservan completed aunque la publicación final sea cancelled/expired; seis pruebas con SQLite real, reloj inyectado y puntos de intercalación fijan esa distinción.
