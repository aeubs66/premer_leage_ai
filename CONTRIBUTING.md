# Contributing

## Set up

On Windows, install Git, uv, and Node.js 20.9 or newer, then run `scripts/bootstrap.ps1`. The script installs Python 3.12, locked project dependencies, the frontend, database migrations, and historical data. It does not train a model unless you pass `-Train`.

## Checks

```powershell
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m ruff format --check src tests
.\.venv\Scripts\python.exe -m mypy src/football_ai
.\.venv\Scripts\python.exe -m pytest
npm.cmd ci --prefix frontend
npm.cmd run lint --prefix frontend
npm.cmd run typecheck --prefix frontend
npm.cmd test --prefix frontend
npm.cmd run build --prefix frontend
```

Use the small synthetic fixtures in `tests/`; do not download data or train models in CI. Review temporal cutoffs, result availability, and split boundaries whenever changing features, calibration, or model selection. Keep source data, model binaries, databases, reports, credentials, and local configuration out of commits. Add dataset and model provenance as small, reviewed JSON manifests when it changes.
