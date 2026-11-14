# Importar el MVP en Jira Cloud

Archivo a importar: `jira-import-mvp-2026-12-06.csv`.

1. En Jira, abre la importación de datos mediante CSV para el proyecto de destino. No uses la creación masiva simple si necesitas conservar la jerarquía de épica, historia y subtarea.
2. Selecciona el archivo CSV y mapea estas columnas:

| Columna del CSV | Campo de Jira |
|---|---|
| `Work item ID` | Work item ID / Issue ID |
| `Parent` | Parent |
| `Work type` | Work type / Issue type |
| `Summary` | Summary |
| `Description` | Description |
| `Priority` | Priority |
| `Status` | Status |
| `Story Points` | Campo personalizado de estimación (si existe) |
| `Labels` | Labels |
| `Due Date` | Due date |

3. Para `Labels`, configura `;` como separador de valores múltiples si el asistente de importación solicita un delimitador. Así se separan, por ejemplo, `mvp-dic-6` e `imagenes`.
4. Si tu proyecto usa nombres de tipos en español, mapea `Epic`, `Story` y `Sub-task` a los tipos equivalentes `Épica`, `Historia` y `Subtarea`.
5. Si no usas puntos de historia, deja `Story Points` sin mapear; las fechas y jerarquías no se perderán.
6. Confirma que las épicas, historias y subtareas aparecen en ese orden. No reordenes las filas antes de importar.

El CSV contiene solo el **MVP comprometido para el 6 de diciembre de 2026**. OCR de placas, atributos avanzados, múltiples líneas y cámara en tiempo real permanecen en el backlog de largo plazo y no se incluyen para proteger la fecha de entrega.

## Verificación posterior

- Abre una historia y confirma que su épica aparece en el campo Parent.
- Abre una subtarea y confirma que su historia aparece en Parent.
- Filtra por la etiqueta `mvp-dic-6` para ver el alcance completo de la entrega.
