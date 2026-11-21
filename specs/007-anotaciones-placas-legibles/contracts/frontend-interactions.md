# Contrato de interacción — 007

## Escena sin obstrucción

El fondo es original_image de 006, obtenido con ApiClient y validado como original canónico. En el recorrido 007 no se solicita anotada para pintar la escena; las rutas históricas permanecen disponibles. Sin original: escena explícitamente no disponible + Reintentar original, lista/ficha autorizadas conservadas. No sustituir por anotada con texto.

La caja usa projectBox sobre proporción natural del original. Se dibujan todos los actores válidos. Solo enrichment_eligible=true es un botón; los demás son contornos sin tabstop ni ficha vehicular. Prohibidos números, etiquetas, pseudo-content textual o iconos de texto dentro de la imagen incluso con selección/hover/foco. Los atributos accesibles no visibles pueden mantener nombres descriptivos.

## Contexto externo

Controles de escena y lista comunican focus/blur y pointerenter/leave con identidad fuente/detección. La banda fuera de la imagen muestra una detección: foco > puntero > selección. Expresa también si es contextual o seleccionada; una tarjeta bajo hover no cambia el detalle seleccionado.

Activación por Enter/Espacio/clic/toque modifica una sola selección. Al salir, vuelve el contexto seleccionado; si no existe, instrucciones. Actualizaciones de resultados no roban foco ni selección. La banda tiene espacio en flujo; IDs con nowrap y nombres envolventes. Anunciar selección, no cada movimiento del ratón; no convertir hover continuo en una avalancha aria-live.

## Catálogo inicial classPresentation

| class_name | Nombre | Color |
|---|---|---|
| car | Automóvil | #2563EB |
| truck | Camión | #D97706 |
| bus | Autobús | #9333EA |
| van | Furgoneta | #0D9488 |
| pickup | Pickup | #DC2626 |
| suv | SUV | #65A30D |
| sedan | Sedán | #DB2777 |
| hatchback | Hatchback | #0891B2 |
| mpv | Monovolumen | #4F46E5 |
| estate | Familiar | #78716C |
| person | Persona | #C2410C |
| bicycle | Bicicleta | #0F766E |
| motorcycle | Motocicleta | #A16207 |
| fuera del catálogo | Nombre recibido + clase no reconocida | #64748B |

Son tokens de presentación, no reglas de clasificación. Registro por nombre normalizado, independiente de class_id, cantidad/orden de resultados. Probar unicidad y estabilidad; agregar nombres conocidos configurados implica ampliar explícitamente esta matriz. El fallback nunca aparenta que una clase desconocida es una de las conocidas.

En escena el trazo de clase permanece visible, acompañado de trazos auxiliares claro/oscuro sin relleno para soportar fondos. Normal: trazo continuo; hover: énfasis de grosor/segmento; selección: doble contorno; foco: halo externo distinguible. El contraste efectivo se comprueba en los componentes reales, no sobre un color fijo de prueba. Texto exterior estándar sobre superficie sólida y muestra de color; no usar texto pequeño del color de clase como única etiqueta.

La leyenda contiene las clases presentes; lista/ficha usan el mismo token y nombre. No dar 44 px a una caja diminuta si invade otra: usar alternativa de lista >=44x44. No modificar orden lógico de foco.

## Comparación de placa

- Al activar una detección con resultado localizado se prepara automáticamente display-contrast-v1. Un resultado aún pendiente muestra Preparando evidencia; sin bbox, no aplicable sin GET.
- Mantener original fiel inicialmente y mostrar Preparando versión procesada sin bloquear el resto. Available permite alternar Original/Procesada con botones de nombres claros y aria-pressed.
- Descripción humana del perfil: contraste local y ampliación cuando corresponde; advertir que ampliación no recupera caracteres ausentes. Si no ayuda, puede volver al original.
- Zoom 1x/2x/4x modifica inspección local; preservar proporción, scroll interno con acceso por teclado y sin scroll horizontal de toda la página. No es un editor ni una nueva fuente.
- Campo separado indica origen de lectura: original/reintento vigente/candidata identificada/desconocido; nunca interpretar la vista activa como variante OCR.
- Elegir modo o zoom no hace llamadas. Selección distinta invalida preview anterior inmediatamente y revoca URL. Reintentar solo la vista procesa el mismo GET con generación nueva.
- Un timeout de visualización no transforma read en unreadable; fallo de OCR tampoco impide recorte si existe localización. Ante acceso/vencimiento se usa retirada de evidencia de 006.
- Si faltan cabecera/versión compatibles, no mostrar PNG sin procedencia como si fuera original; mantener original autorizado y explicar incompatibilidad.

## Matriz de pruebas

US1/US2: >=10 escenas, >=3 densas de21, IDs de1/2/3 cifras, cajas pequeñas/solapadas y actores no enriquecibles. En tres viewports y texto200%, demostrar cero texto sobre imagen por DOM y píxeles del original, imagen anotada distinta no usada, prioridad/contexto/ficha estable, leyenda y catálogo coherentes. Revisar manualmente capturas y medir contraste real; respetar movimiento reducido.

US3: >=30 placas localizadas con geometrías distinguibles; cuatro estados de lectura; pérdida de original, fallos/cuerpos suspendidos, metadatos inválidos/misma detección de otra fuente, reset/cambio credencial/TTL durante decode. Confirmar cero POST nuevos al alternar/reintentar preview y ninguna restauración tardía.

Los tiempos se miden con reloj monotónico desde la activación hasta render de identidad/imagen correcta decodificada, separando primera carga/caché. No afirmar precisión de OCR con fixtures.
