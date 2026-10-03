# Getting started on Windows

Open PowerShell in `D:\premer_leage_ai`. Python 3.12 and Node 24 are available on this laptop. Use uv rather than the Windows Store Python alias.

```powershell
cd D:\premer_leage_ai
uv sync --python 3.12 --extra ml --extra neural --extra tracking --extra api --extra dev
Copy-Item .env.example .env
.\.venv\Scripts\Activate.ps1
football-ai update-data
football-ai train
football-ai evaluate
football-ai backtest
football-ai predict-upcoming
football-ai api
```

If activation is unavailable, run `.\.venv\Scripts\python.exe -m football_ai` followed by the command. You need not change the machine's execution policy. `uv run --no-sync football-ai COMMAND` also uses the prepared environment without removing extras.

In a second PowerShell window:

```powershell
cd D:\premer_leage_ai\frontend
npm.cmd ci
npm.cmd run dev
```

Open http://127.0.0.1:3000. API documentation is at http://127.0.0.1:8000/docs. Both services bind to loopback by default. No system service is installed.

## Data and options

`update-data --offline` reuses cached results. `update-data --csv PATH --season 2024/2025` imports your data. `update-data --fixtures PATH` imports an alternate fixture file. `update-data --api-fixtures` uses `FOOTBALL_DATA_TOKEN` from the process environment. A provider may publish only a short upcoming window; an empty fixture list is a real data state.

Default training is LIGHT/FAST with CPU PyTorch. `train --no-neural` omits neural candidates; `train --no-tune` uses configured tree parameters; `train --optimization NORMAL` expands tuning. A second `train` creates a candidate rather than silently replacing the champion. Use `retrain` for the independent comparison gate. Use `rollback` to restore the previous champion.

Reports are in `reports/<version>/report.html`. MLflow is local:

```powershell
.\.venv\Scripts\mlflow.exe ui --backend-store-uri sqlite:///D:/premer_leage_ai/mlruns/tracking.db --host 127.0.0.1
```

Set `FOOTBALL_AI_DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST/DATABASE` and install the `postgres` extra to use an existing PostgreSQL instance. Never commit credentials. `TEST_DATABASE_URL` must name a dedicated disposable test database.
