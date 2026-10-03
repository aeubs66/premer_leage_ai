# Getting started on Windows

Install Git, uv, and Node.js 20.9 or newer. Clone the private repository and run the Windows bootstrap. uv installs a managed Python 3.12 runtime when needed.

```powershell
git clone <private-repository-url>
cd premer_leage_ai
.\scripts\bootstrap.ps1
```

Bootstrap installs locked Python and frontend packages, creates `.env` only when missing, creates local directories, migrates SQLite, downloads and validates historical data, rebuilds chronological features, and checks API health. It does not train unless you pass `-Train`. Use `-SkipData` for offline setup. If download fails, import a result CSV as described below. Existing `.env` is preserved; its values are never committed.

Run individual commands with `\.venv\Scripts\python.exe -m football_ai COMMAND` from the repository root. PowerShell activation is optional; no system execution-policy change is needed.

Start the API:

```powershell
\.venv\Scripts\python.exe -m football_ai api
```

In a second terminal:

```powershell
cd frontend
npm run dev
```

Open http://127.0.0.1:3000. API reference: http://127.0.0.1:8000/docs. Both servers bind to loopback by default.

## Data and training

`update-data --offline` reuses cached historical results. `update-data --csv PATH --season 2024/2025` imports a local result CSV. `update-data --fixtures PATH` imports fixture data. `update-data --api-fixtures` uses `FOOTBALL_DATA_TOKEN` from the environment or `.env`. An empty fixture list reflects actual source coverage.

LIGHT/FAST CPU settings are the defaults. `train --no-neural` omits the neural learner; `train --no-tune` uses configured tree parameters; `train --optimization NORMAL` expands tuning. Running `train` with an existing champion saves a candidate. `retrain` applies the independent champion-comparison gate. `rollback` restores the previous champion.

Reports are in `reports/<version>/report.html`. MLflow tracking is local:

```powershell
\.venv\Scripts\mlflow.exe ui --backend-store-uri sqlite:///D:/premer_leage_ai/mlruns/tracking.db --host 127.0.0.1
```

Set `FOOTBALL_AI_DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST/DATABASE` in local `.env` and install the `postgres` extra to use an existing PostgreSQL server. `TEST_DATABASE_URL` must point to a dedicated disposable test database.

## Moving local state

The database and trained model binaries are ignored by Git. To preserve saved predictions and results on another PC, stop the API and make a private local backup of `data/football.db`, `models/`, and `data/processed/`; restore those files only into the matching project version. Keep `.env`, credentials, raw downloads, caches, reports, and MLflow files separate. The project currently does not provide a versioned export/import tool.

See [reproducibility.md](reproducibility.md) for the ignored-file inventory and recovery notes.
