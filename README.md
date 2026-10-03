# Premier League AI

A Windows-native football forecasting and AI engineering platform. Priorities: temporal correctness, probability evaluation, reproducibility, clear explanations.

The original requirements are in `docs/project-specification.txt`; the system design is in `docs/architecture.md`.

Implemented: downloadable/cached CSV results and fixtures, optional API adapter, time-aware features, baselines/Elo/Poisson/Dixon–Coles/XGBoost/PyTorch, bounded Optuna tuning, time-safe ensembles/calibration, walk-forward reports, local MLflow, SQLite/PostgreSQL architecture, immutable prediction records, FastAPI, and a responsive analytics dashboard.

## Run locally

```powershell
cd D:\premer_leage_ai
uv sync --python 3.12 --extra ml --extra neural --extra tracking --extra api --extra dev
.\.venv\Scripts\python.exe -m football_ai update-data
.\.venv\Scripts\python.exe -m football_ai train
.\.venv\Scripts\python.exe -m football_ai evaluate
.\.venv\Scripts\python.exe -m football_ai predict-upcoming
.\.venv\Scripts\python.exe -m football_ai api
```

In another terminal:

```powershell
cd D:\premer_leage_ai\frontend
npm.cmd ci
npm.cmd run dev
```

Dashboard: http://127.0.0.1:3000 · API docs: http://127.0.0.1:8000/docs. The package also exposes `football-ai` when its environment is activated. Use `uv run --no-sync` if invoking it through uv without repeating dependency extras.

## Research safeguards

No odds in core features. No betting functions. Missing statistics remain missing. Each historical feature uses only prior available observations. The latest complete season is sealed for final evaluation. Training, calibration, and ensemble fitting use temporal separation and OOF predictions. Production refits are stored separately from research evaluation models.

Confidence displays probability, entropy, disagreement, sample counts, and calibration diagnostics. It never guarantees an outcome. Source limitations and poor results stay visible in saved reports.

## Learn and operate

- `docs/getting-started.md`: setup, profile choices, data imports, and local MLflow.
- `docs/study-guide.md`: ordered code-reading path, mathematics, questions, exercises.
- `docs/data-leakage.md`: temporal rules, tests, and limitations.
- `docs/automation.md`: update/retrain/record workflows and optional Windows scheduling.
- `docs/verification.md`: measured results and validation limits from this build.

Optional enrichment uses timestamped JSON Lines; xG and player information are not guaranteed by free sources. Empty upcoming fixture lists reflect actual source coverage. Configure `FOOTBALL_DATA_TOKEN` or import alternate fixtures if needed.

## Checks

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\ruff.exe check src tests
.\.venv\Scripts\ruff.exe format --check src tests
.\.venv\Scripts\mypy.exe src/football_ai
cd frontend
npm.cmd run lint
npm.cmd run typecheck
npm.cmd test
npm.cmd run build
```

PostgreSQL requires an existing server and the `postgres` extra. Its integration test runs only with `TEST_DATABASE_URL` pointing at a dedicated test database. Optional experiments need a hypothesis, data sufficiency, and CPU budget; expensive neural architectures are not implemented by default.
