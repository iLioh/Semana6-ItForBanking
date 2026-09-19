# Plan del Laboratorio 06

## Fase 1 — Preparación local

- Extraer exclusivamente `LAB06_datasets_definitivos.zip` sin modificar etiquetas humanas.
- Caso 1: `kyc_v1` → `scoring_v1` → `explainability_v1` → decisión humana. Python calcula referencia académica independiente.
- Caso 2: `classification_v1` y `classification_v2` → golden humano aislado → métricas → `response_v1` → revisión humana.
- Adaptar modelos, contratos, API, frontend y migración local.
- Validar datasets, pruebas con mock/fake, lint y build.
- No modificar Azure ni ejecutar inferencias reales.

## Fase 2 — Pendiente de autorización/ejecución posterior

1. Confirmar base y Blob objetivo; respaldar datos.
2. Limpiar datos de ejecución con `scripts/reset_lab06_data.py` y confirmación explícita.
3. Aplicar migración `20260919_0002` en Azure SQL.
4. Cargar CSV oficiales con `scripts/seed_official_datasets.py --apply --yes`.
5. Desplegar versión nueva y verificar acceso/seguridad.
6. Ejecutar los 15 casos del Caso 1 y la evaluación V1/V2 de las 30 quejas en Azure OpenAI.
7. Registrar métricas reales y pruebas de revisión humana. No inventar ni ajustar golden.
