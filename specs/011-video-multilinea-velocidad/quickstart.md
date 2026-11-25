# Guía de validación de011

Esta fase solo genera documentos. Los comandos de pruebas nuevos indicados abajo son objetivos para implementar; todavía no existen sus fixtures/módulos. No iniciar servidores ni modificar .env privado para validar la planificación.

## Antes de implementar

1. Confirmar checkout principal y rama feature/011-video-multilinea-velocidad; conservar cambios previos y sesiones ajenas.
2. Leer spec/plan/research/data-model y contracts. Generar tasks con trazabilidad26FR/10SC, separando referencia, implementación, pruebas automáticas y validación humana.
3. Primera tarea, antes de editar producto: crear y ejecutar comparador sintético011 de escritura única que mida referencia actual de publicación, con hash del código, versiones, hardware/configuración, un calentamiento y cinco muestras. No reusar ni sobrescribir la referencia010. Objetivo de ruta: backend/tests/performance/test_count_lines_overhead.py con modos capture/compare. No afirmar que existe o que ya se ejecutó.
4. Declarar regex como dependencia directa y fijar lock en implementación. Sin dependencia transitiva ni instalación desde plan. Mantener Python 3.12; no recrear entorno con3.15.

## Desarrollo y arranque de producto

Cuando la implementación esté lista, desde la raíz del checkout principal se mantienen los scripts existentes, en terminales separadas:

```powershell
.\backend\start.ps1 -Service api
```

```powershell
.\backend\start.ps1 -Service gateway
```

```powershell
npm --prefix frontend run dev
```

Si ya estás dentro de frontend, usar `npm run dev`. No arrancar instancias duplicadas en los mismos puertos. Configuración privada se conserva; límites nuevos defaults10 activas/128 admitidas se anuncian en descriptor y se documentarán como opciones backend sin secretos.

## Comprobaciones automáticas previstas

Desde raíz, después de implementar las tareas y generar los tests:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests
npm --prefix frontend test
npm --prefix frontend run build
```

Desde frontend, fixture/browser config011 aislados que deberán crearse para no leer secretos ni depender del video privado:

```powershell
npx playwright test --config playwright.011.config.ts --project desktop
npx playwright test --config playwright.011.config.ts --project tablet --project mobile
```

Añadir pruebas contractuales de las cuatro operaciones y del relay: cuerpos/query inválidos, semántica, revisión segura, ownership/generación/TTL y no-store/CSRF. Los contratos anteriores deben conservar sus respuestas. Incluir imagen/video de regresión y adaptación explícita del caso010 que esperaba el botón de dirección.

## Demostración funcional controlada

1. En fixture011 de intersección con las seis clases y movimientos opuestos, dibujar AV SIMÓN BOLIVAR y RUTA VIVA en el primer fotograma. Agregar hasta diez líneas y confirmar nombres/colores únicos, arrastre suave de extremos/segmento y teclado.
2. Iniciar análisis: tarjetas por encima de la escena, sin flecha ni «Invertir sentido». Un cruce desde cualquier lado suma una unidad en su línea; un mismo vehículo puede sumar en dos líneas. Contactos/prolongaciones/predicción no suman.
3. Recolorear y renombrar una desde su tarjeta: demás líneas y conteos estables. Mover solo una: solo su tarjeta pasa a pending y se reconstruye. Borrar una, simular respuesta tardía y recargar: no reaparece.
4. Con tramo completo de30 s y referencia reproducible en el equipo, medir0,5×/1×/2×:60/30/15 s con tolerancia5%. Cambiar velocidad mientras está pausado conserva cuadro y crop. Comprobar mismos tiempos fuente/cajas/cantidades. Registrar condiciones cuando el equipo no sostiene reproducción, sin atribuirlo al detector.
5. Ejecutar diez ciclos de buscar atrás/adelante y veinte intentos fuera del prefijo a distintas velocidades: cero cantidades futuras, duplicados o cuadros no analizados. Alcanzar el límite a 2×, esperar y pausar explícitamente: no reanudar contra la intención del usuario.
6. Reabrir trabajo con línea anterior direccional: conservar segmento, nuevo nombre/color y recalcular ambos sentidos; si faltan observaciones, mensaje de nuevo análisis. Borrar importada y reabrir: no reimportarla.
7. Probar360/768/1440px, toque, foco/teclado y fullscreen; tarjetas/velocidad visibles sin cubrir escena ni overflow de página. Envencimiento/retirada se limpia todo sin ampliar el plazo.

## Rendimiento y evidencia

Capture/compare del futuro comparador011, nunca del benchmark010: mismo fixture300 cuadros×20 observaciones, medición0/1/10 líneas, steady-state y catch-up separados. Guardar entorno/hashes, tiempos de publicación, lock/captura/cómputo/commit, p95 GET, retraso de cobertura y memoria. Objetivos iniciales: sección crítica p95≤10 ms, GET≤250 ms, catch-up10 líneas≤5s en fixture; ajuste de lotes si no se cumplen. Comparación0líneas frente a referencia>5% requiere investigación documentada AB/BA, sin borrar el resultado desfavorable.

No etiquetar estos tiempos como FPS de inferencia. Un nuevo perfil ordinario puede añadirse posteriormente manteniendo pesos/hilos/intervalo, sin ejecutar por defecto la comparación larga diferida. No se cierra ningún pendiente humano/real anterior por un benchmark sintético.

La entrega implementada deberá guardar agregados en evidence/ con IDs de caso, versión, resultado y límites; sin videos del usuario, cuadros, rutas privadas, placas ni secretos. SC-009 requiere cinco personas: registrar resultado real o pendiente, nunca sustituirlo por tests automáticos. Actualizar docs/registro-evolucion-sistema.md y commits por etapa.


Agregar una regresión de intervalo de cantidad: reproducir a30cuadros/s con consultas400ms, y comprobar que una respuesta anterior mantiene un número exactamente válido solo hasta valid_until_us (siguiente cruce/cobertura/prefijo). Al agotarse, demanda agrupada sin más de una petición en vuelo; las otras tarjetas válidas permanecen visibles. No se exige una petición por cuadro ni se presenta el cero pendiente como conteo.
