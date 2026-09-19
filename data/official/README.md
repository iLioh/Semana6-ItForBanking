# LAB06 — Datasets definitivos

## Regla principal
Todos los datos de estos archivos son SIMULADOS y se utilizan únicamente con fines académicos.
Los nombres de empresas son ficticios o corresponden a los nombres de ejemplo de la guía del laboratorio.
No se atribuyen estados financieros ni conductas reales a empresas existentes.

## Caso 1 — Onboarding + Scoring + Explainability
Archivo de entrada:
- `case1/empresas_simuladas.csv`
- 15 empresas.
- Incluye datos KYC simulados y variables financieras simuladas.

Archivo de referencia:
- `case1/referencia_academica.csv`
- NO debe enviarse al LLM.
- Sirve para contrastar el KYC y el scoring obtenidos.

### Flujo esperado
Datos -> Prompt KYC -> Prompt Scoring -> Prompt Explainability -> Decisión humana

### KYC de referencia
Reglas académicas usadas solo para la referencia:
- RECHAZADO: lista restrictiva, beneficiario final no identificado, origen no declarado o actividad incoherente.
- OBSERVADO: documentación incompleta, relación PEP o sustento parcial del origen de fondos.
- APROBADO: caso restante.

### Scoring de referencia
- Liquidez >= 1.5 = 25; >= 1.0 = 15; < 1.0 = 5.
- Endeudamiento <= 0.50 = 25; <= 0.70 = 15; > 0.70 = 5.
- Flujo POSITIVO = 25; VARIABLE = 15; NEGATIVO = 5.
- Historial BUENO = 25; REGULAR = 15; MALO = 5.
- 80-100: BAJO / APROBAR.
- 50-79: MEDIO / EVALUAR.
- <50: ALTO / RECHAZAR.

La referencia académica no es una política crediticia real.

## Caso 2 — Clasificador de quejas
Archivo de entrada:
- `case2/quejas_bancarias_30.csv`
- 30 casos, el máximo planteado por la guía.
- 10 FRAUDE, 10 SERVICIO y 10 PRODUCTO en el golden.
- Los textos de entrada NO incluyen la etiqueta.
- Hay casos fáciles, medios y ambiguos.

Archivo golden:
- `case2/golden_humano_30.csv`
- NO debe enviarse al LLM.
- Fue definido antes de ejecutar el modelo.
- Permite medir Accuracy, Precision, Recall, F1, matriz de confusión y errores por categoría.

## Cómo usar para V1 vs V2
1. Ejecutar Prompt V1 sobre los 30 casos.
2. Persistir resultados.
3. Ejecutar Prompt V2 sobre EXACTAMENTE los mismos 30 casos.
4. Persistir resultados por separado.
5. Comparar ambos contra `categoria_golden`.
6. No modificar el golden después de conocer las respuestas del modelo.
7. No forzar que V2 obtenga mejores métricas; reportar el resultado real.

## Human-in-the-loop
Caso 1:
- KYC generado.
- Score/riesgo/recomendación.
- Explicabilidad.
- Decisión humana independiente.
- Estado de revisión: PENDIENTE / REVISADA.

Caso 2:
- Clasificación IA.
- Golden humano solo para evaluación.
- Borrador de respuesta separado.
- Revisión humana del borrador.
- Para FRAUDE la revisión humana debe ser obligatoria.

## Limpieza de Azure
Cuando se migre a esta versión:
- eliminar resultados antiguos de ejecuciones equivocadas;
- conservar infraestructura, tablas y migraciones;
- cargar solo estos datasets como versión oficial;
- ejecutar nuevamente V1/V2 para obtener métricas limpias.
