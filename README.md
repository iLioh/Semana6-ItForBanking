# IBLaboratorio06 · IA generativa y Prompt Engineering en banca

Demostración académica con **datos simulados**. Los resultados no constituyen decisiones crediticias ni resoluciones reales de una entidad financiera.

## Flujos oficiales

1. **Onboarding y Scoring Empresarial:** 15 empresas simuladas → prompt `kyc_v1` → prompt `scoring_v1` → prompt `explainability_v1` → decisión humana. El score lo produce la IA; Python calcula una **referencia académica independiente** para detectar discrepancias, sin sustituir ni corregir silenciosamente el resultado IA.
2. **Clasificación de Quejas Bancarias:** 30 quejas simuladas → `classification_v1` y `classification_v2` → comparación posterior con **golden humano** 10 FRAUDE / 10 SERVICIO / 10 PRODUCTO → accuracy, precision, recall, F1, matriz de confusión y análisis de errores → `response_v1` → revisión humana. El golden nunca se envía al modelo.

Los archivos proceden **exclusivamente** de `LAB06_datasets_definitivos.zip` y se organizan en [`data/official/`](data/official/README.md). Los nombres de ejemplo y todas las variables son simulados. Las referencias no son políticas bancarias reales.

## Arquitectura

React + TypeScript/Vite llama a FastAPI. SQLAlchemy/Alembic guardan resultados, versiones de prompt, modelo y revisión; Blob privado almacena los CSV oficiales en la futura fase de despliegue; Azure OpenAI ejecutará las inferencias reales. App Service usa Managed Identity/RBAC y Application Insights en la arquitectura cloud. El entorno Azure existente todavía ejecuta la **versión anterior**: esta Fase 1 no desplegó ni modificó Azure.

La demo cloud actual restringe acceso por IP, **no autentica personas individualmente**. No es un entorno bancario productivo; Entra ID para usuarios, red privada/Private Endpoints y revisión de seguridad quedan pendientes si se busca producción real.

## Trabajo local sin consumir Azure

Requisitos: Python 3.12, `uv`, Node.js. Configurar `.env` local con `APP_ENV=local`, `AI_PROVIDER=mock`, `AUTH_REQUIRED=false` y `DATABASE_URL=sqlite:///./outputs/lab06.db`. No copiar credenciales a Git.

```bash
uv sync --locked
uv run python scripts/seed_official_datasets.py
uv run alembic upgrade head
uv run uvicorn src.app.main:app --reload
```

En otra terminal: `cd frontend`, `npm ci`, `npm run dev`. Swagger: `http://localhost:8000/docs`.

API principal: `GET /api/v1/case1/companies`, `POST /api/v1/case1/run`, `GET /api/v1/case1/results`, `PATCH /api/v1/case1/results/{id}/human-review`, `GET /api/v1/case2/cases`, `POST /api/v1/case2/classify`, `POST /api/v1/case2/evaluate`, `GET /api/v1/case2/metrics`, `PATCH /api/v1/case2/predictions/{id}/human-review`.

Los porcentajes producidos por el proveedor mock **no son métricas reales**. La UI muestra “PENDIENTE DE EVALUACIÓN” hasta ejecutar Azure OpenAI en Fase 2.

## Verificación

```bash
uv run ruff check src scripts/check_environment.py scripts/seed_official_datasets.py scripts/reset_lab06_data.py tests
uv run pytest
uv run python scripts/check_environment.py
uv lock --check
cd frontend
npm run lint
npm test
npm run build
```

`scripts/reset_lab06_data.py` y `scripts/seed_official_datasets.py --apply --yes` están **preparados para Fase 2**, pero no se ejecutan en Fase 1. Antes de Fase 2: respaldar/verificar la base objetivo, limpiar datos de ejecución, aplicar la migración `20260919_0002`, cargar los CSV oficiales, desplegar y medir con IA real. Nunca usar métricas mock como evidencia del modelo.

Más detalle: [`docs/architecture.md`](docs/architecture.md), [`docs/security.md`](docs/security.md), [`docs/data-dictionary.md`](docs/data-dictionary.md) y [`ppt.md`](ppt.md).
