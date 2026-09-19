# Laboratorio 06 — Guion para presentación

## 1. Problema

Un banco necesita revisar información de empresas y ordenar quejas de clientes. Hacerlo manualmente puede ser lento e inconsistente; automatizar decisiones sin control puede generar errores y sesgos.

## 2. Propuesta

Un prototipo académico de IA **asistiva**, no decisoria. Trabaja con datos simulados, produce resultados estructurados y explicables, conserva trazabilidad y exige que una persona revise el resultado.

## 3. Tecnologías

- React + TypeScript/Vite: interfaz de la demo.
- FastAPI + Pydantic: API y validación de resultados IA.
- SQLAlchemy + Alembic: persistencia y migraciones; SQLite local, Azure SQL en la futura Fase 2.
- Azure Blob Storage: datasets oficiales privados en cloud.
- Azure OpenAI: inferencia real en Fase 2; mock determinístico en desarrollo y pruebas locales.
- Azure App Service, Managed Identity/RBAC y Application Insights: hospedaje, acceso entre servicios y observabilidad cloud.

## 4. Caso 1 — Onboarding y Scoring Empresarial

15 empresas simuladas, incluidos AgroPerú SAC, TechNova SRL, Minera Andina y Constructora Andina SAC.

1. Prompt `kyc_v1`: estado APROBADO, OBSERVADO o RECHAZADO según señales KYC simuladas.
2. Prompt `scoring_v1`: calcula 0–100 usando **solo** liquidez, endeudamiento, flujo e historial simulados. Propone riesgo y recomendación.
3. Python calcula una **referencia académica independiente** para detectar discrepancias; nunca reemplaza silenciosamente el score IA.
4. Prompt `explainability_v1`: explica variables, límites y posibles sesgos sin recalcular.
5. Una persona registra su decisión, distinta de la recomendación IA.

## 5. Caso 2 — Clasificación de Quejas Bancarias

30 quejas simuladas. Las categorías son FRAUDE, SERVICIO y PRODUCTO. Una persona definió previamente un **golden humano** balanceado 10/10/10.

1. `classification_v1` es una línea base válida.
2. `classification_v2` añade reglas de ambigüedad y restricciones.
3. Ambos clasifican exactamente los mismos textos **sin ver el golden**.
4. Tras inferir, se calcula accuracy, precision, recall, F1 macro y por clase, matriz de confusión y errores.
5. `response_v1` redacta un borrador prudente por separado; una persona valida, corrige o rechaza.

## 6. Seguridad y ética

Todos los datos oficiales son simulados y proceden de `LAB06_datasets_definitivos.zip`. No hay verificaciones KYC reales, aprobación crediticia ni confirmación de fraude. Las referencias humanas no se envían a los prompts. La demo cloud existente está restringida por IP, pero no tiene autenticación individual ni red privada productiva.

## 7. Cómo se llegó a la solución

Se partió de la guía del curso, se normalizaron dos flujos y sus contratos, se separaron entradas de referencias, se implementó trazabilidad de prompts/modelo y revisión humana, y se validó todo localmente con proveedor IA falso y pruebas automatizadas. No se alteraron etiquetas humanas para mejorar resultados.

## 8. Pruebas a mostrar

- En local: ejecutar una empresa y mostrar KYC, score IA, referencia, XAI y decisión humana persistida.
- En local: clasificar una queja y mostrar categoría, confianza, borrador y revisión.
- Mostrar que la UI marca las métricas reales como **PENDIENTE DE EVALUACIÓN** en Fase 1.
- Tras Fase 2: repetir en Azure y presentar métricas **reales** V1/V2, matriz y casos errados. No afirmar cifras antes de esa ejecución.
