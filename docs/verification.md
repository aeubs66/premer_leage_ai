# Delivery verification — 3 October 2026

The implementation is saved directly in `D:\premer_leage_ai`, with local dependencies, versioned real data, trained artifacts, reports, and Git checkpoints.

## Executed checks

- Python: 27 tests passed; one PostgreSQL test skipped because `TEST_DATABASE_URL` is not configured.
- Ruff lint and formatting pass; mypy reports no issues across 48 source files.
- Frontend: lint, TypeScript, three Vitest tests, and production build passed.
- The revised JavaScript dependency audit reported zero vulnerabilities, including development dependencies.
- Real CSV update ingested 1,570 records spanning 2022/2023 through 2026/2027. Repeating an offline update added zero duplicates and changed zero records.
- Full LIGHT/FAST CPU training ran with XGBoost, Optuna, PyTorch, ensembles, calibration alternatives, and local MLflow. A second run exercised source archiving and feature diagnostics from a clean committed source state.
- The fixture downloader, empty upcoming-prediction workflow, result attachment with no pending results, prospective evaluation, and unchanged-data retraining rejection ran successfully.
- The isolated end-to-end test fits actual models on explicitly synthetic test records, saves a forecast, validates exact tree SHAP and score coherence, rejects direct SQL mutation, attaches a result separately, and evaluates it. Synthetic test records never enter the real project database.
- The live API returned successful health, team-form, and performance responses. Browser inspection confirmed the dashboard and measured research page render correctly.

## Measured research results

Initial champion: `64bb78bed878432b`. Selection chose a small meta ensemble containing Elo, Poisson, XGBoost, and the neural network. No calibration transform improved selection log loss. The ensemble was not changed based on the final test.

| Evaluation | Matches | Log loss | Brier | Winner accuracy |
|---|---:|---:|---:|---:|
| Sealed 2025/2026 test | 380 | 1.0303 | 0.6195 | 47.37% |
| Monthly frozen-recipe walk-forward | 380 | 1.0264 | 0.6172 | 48.16% |

Initial reports: `reports/64bb78bed878432b/report.html` and its `walk-forward` subdirectory. The source-archived diagnostic candidate is `2b56024500ad43a6`; its report includes 149 permutation-importance rows, feature-importance plot, reliability plots, OOF predictions, measured outcomes, and `source.zip`. It remains a candidate; the existing champion is preserved.

## Practical limits

The published fixture CSV contained no Premier League fixtures during verification. Real upcoming forecasts therefore await a populated fixture source: alternate CSV import or the optional token-authenticated API. No upcoming matches or predictions were invented.

xG and player availability are missing from the initial source and are shown as unavailable. Historical result-publication times are inferred under the documented conservative policy. Administrative points deductions are not reconstructed. PostgreSQL schema support and tests are implemented, but an actual server connection has not been verified on this laptop.

Two test warnings are external diagnostics: a TestClient dependency deprecation and balanced-accuracy behavior on a one-match synthetic evaluation. Neither is a failing check or a measured real-data result.

Automatic approval review blocked deletion of a temporary dependency backup. It remains under the ignored `work/node_modules_previous` directory and is not used by the application. No cloud service, scheduled task, or external deployment was created.
