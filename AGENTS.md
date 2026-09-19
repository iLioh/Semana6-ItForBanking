# Repository Guide

## Environment and safety

- Python 3.12, `uv` and `uv.lock`; use `uv run`, never bare `pip`. If `uv.exe` is blocked by the host, use the already synchronized `.venv/Scripts/python.exe` for verification.
- Keep Azure credentials only in ignored `.env`. Never print or commit secrets.
- Phase 1 is local-only: no Azure deploy, SQL/Blob write, firewall change or real OpenAI calls. Tests must use fakes.

## Official datasets and semantics

- Use **only** the CSVs extracted from `LAB06_datasets_definitivos.zip` under `data/official/`. All examples are simulated.
- Caso 1 has 15 companies. Its `referencia_academica.csv` is a comparison aid, never a prompt input. Python reference scoring may not replace the LLM score. Expose independent IA recommendation, human decision and review status.
- Caso 2 has 30 complaints and `golden_humano_30.csv` with 10 FRAUDE, 10 SERVICIO and 10 PRODUCTO. Load golden only after inference, never in provider context. Keep classification and response generation separate.
- Do not alter human labels to improve metrics. Mock metrics are not real model results.

## Code boundaries

- `src/app/official_data.py` loads official CSVs; `src/app/academic_reference.py` owns independent reference rules.
- `src/app/ai.py` owns prompt contracts and mock/Azure providers. Versioned prompts live in `prompts/case1/` and `prompts/case2/`.
- `src/app/case1.py` and `src/app/case2.py` own pipelines; `src/app/routes.py` exposes FastAPI endpoints; SQL models/migrations live in `src/app/models.py` and `migrations/`.
- Frontend React code lives in `frontend/src/`. Keep prompts, Pydantic, SQL and UI contracts aligned.

## Verification

- Lint changed Python: `uv run ruff check src scripts/check_environment.py scripts/seed_official_datasets.py scripts/reset_lab06_data.py tests`.
- Run `uv run pytest`, then `uv run python scripts/check_environment.py`. Never add `--azure` during Phase 1.
- Frontend: `npm run lint`, `npm test`, `npm run build`.
- `uv lock --check` after dependency changes. Avoid unnecessary repeated full-suite runs.
