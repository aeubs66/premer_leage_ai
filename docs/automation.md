# Updates, retraining, and local operation

`update-data` validates fresh results, versions changed data, updates SQL state, and caches historical features/Elo. Duplicates do not create new matches. Source corrections create a different dataset version. `predict-upcoming` saves a new snapshot for each eligible fixture. `record-results` attaches outcomes. `evaluate-predictions` summarizes prospective performance by model version.

`train` initializes the first champion but does not silently replace an existing one. `retrain` fits a candidate, then seeks at least 40 genuinely new completed matches after the champion's training cutoff. Both recipes are replayed on a common prefix before that window. Promotion requires lower log loss and non-worse Brier. If candidate selection overlaps the comparison period, promotion is deferred until an independent future window. Existing champion versions remain available; `rollback` changes the atomic pointer.

Optional Windows Task Scheduler: create a task with program `D:\premer_leage_ai\.venv\Scripts\python.exe`, arguments `-m football_ai update-data`, and starting directory `D:\premer_leage_ai`. Add separate tasks for `predict-upcoming`, `record-results`, and `evaluate-predictions` at your chosen times. Set “Do not start a new instance” to prevent overlapping writers. Use environment variables for secrets and retain logs. No scheduled task is created automatically.

The API runs locally. PostgreSQL is supported but a server must be supplied separately. For remote deployment, add authentication, HTTPS, backups, and access restrictions before exposing prediction-writing endpoints. This project does not claim to implement a public hosted service.
