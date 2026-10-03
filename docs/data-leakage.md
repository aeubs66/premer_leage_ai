# Preventing football data leakage

A feature asks what could have been known at a particular moment. A match's final statistics are its training label/context for subsequent games, not inputs to its own prediction.

The replay engine sorts results by `available_at`. Before reading a fixture's features it applies only results with `available_at < cutoff`. Equal timestamps are excluded. Live features use generation time rather than the future kickoff, preventing a future lineup or intervening match from entering today's forecast.

Common mistakes:

- Rolling goals that include the current match. In dataframe implementations, shift each team's history before rolling, expanding, or weighting.
- Final-season tables, current web standings applied to old dates, or externally calculated Elo using future matches.
- Filling missing values or fitting scalers on the complete dataset. Imputation and scaling belong inside each training fold.
- Random train/test splitting, or splitting simultaneous fixtures across stages.
- Stacking predictions made on the same rows used to train the base model.
- Calibrating on test labels, then calling the same test an independent evaluation.
- Downloading today's injury history and pretending it was available before old matches.
- Replaying a model fitted in 2026 against 2023 matches and calling it a historical pre-match forecast.

Tests mutate current/future scores and xG, delay availability, check simultaneous fixtures, compare training and inference engines, and check fitted preprocessing remains unchanged by validation inputs. Inspect `tests/test_features.py`, `test_training.py`, and `test_learners.py`.

The newest complete season is never used for recipe decisions. After its frozen evaluation, a separate production artifact may refit the chosen recipe on all completed games. Its training cutoff is recorded. Research and production artifacts cannot be interchanged in backtesting.

Limitations: inferred result publication times cannot prove real historical availability; later source corrections can change retrospective records; reconstructed sporting tables do not model administrative point deductions. Reports disclose these limits. Do not use optional sources that cannot meet the temporal contract.
