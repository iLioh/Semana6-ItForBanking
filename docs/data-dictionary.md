# Diccionario de datos oficiales

Origen: [`LAB06_datasets_definitivos.zip`](../LAB06_datasets_definitivos.zip). Archivos extraídos sin alterar etiquetas en [`data/official/`](../data/official/README.md). Todos los campos de entrada son **SIMULADOS**.

## Caso 1

| Campo | Significado | Uso |
|---|---|---|
| `empresa_id`, `empresa`, `sector`, `region`, `pais` | Identificación ficticia/contexto | UI y KYC; **no** cálculo del score |
| `documentacion_legal`, `beneficiario_final_identificado`, `origen_fondos`, `actividad_coherente`, `coincidencia_lista_restrictiva`, `pep_relacionado` | Señales KYC simuladas | Prompt `kyc_v1` |
| `liquidez`, `endeudamiento`, `flujo`, `historial_crediticio` | Variables financieras simuladas | Únicas entradas del prompt `scoring_v1` |
| `reference_score`, `kyc_reference` | Referencia académica calculada por Python | Comparación posterior, nunca entrada IA |
| `score`, `risk_level`, `recommendation` | Resultado IA | No constituye decisión real |
| `human_decision`, `review_status` | Decisión y estado humano | `APROBAR/EVALUAR/RECHAZAR`; `PENDIENTE/REVISADA` |

El archivo de referencia académica conserva los nombres de columna originales del ZIP por integridad. En la aplicación y la presentación se denomina únicamente **referencia académica**; no se cambian las etiquetas originales.

## Caso 2

| Campo | Significado | Uso |
|---|---|---|
| `caso_id`, `asunto`, `cuerpo`, `dificultad` | Queja simulada | Entrada IA, UI y análisis de errores |
| `categoria_golden`, `prioridad_golden`, `justificacion_golden` | Etiquetas humanas originales del ZIP | Solo evaluación posterior, nunca prompt |
| `category`, `confidence`, `priority`, `summary`, `rationale`, `secondary_category`, `ambiguity_detected` | Clasificación IA | Contrato común V1/V2 |
| `draft_response` | Borrador generado por prompt separado | Revisión humana antes de uso |
| `human_category_correction`, `review_status` | Corrección/estado humano | No sobrescribe categoría IA |

Categorías oficiales: `FRAUDE`, `SERVICIO`, `PRODUCTO` (10 referencias humanas por clase).
