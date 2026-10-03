# Historical backtesting

Read `training/splits.py`, `training/trainer.py`, and `services.py`. Outer validation simulates expanding training prefixes and produces chronological OOF records. Each fold stores training IDs, prediction IDs, latest usable result time, and prediction cutoff.

`football-ai backtest` loads the research artifact's frozen recipe and original dataset snapshot. It refits base models monthly using only results available before the next fixture, then predicts that fixture using the same historical feature engine. Meta and calibration parameters remain frozen before the final season. Predictions, model version, cutoff, probabilities, and actual result are saved to a retrospective report.

This is different from prospective evaluation. Backtest records were reconstructed later; prospective records were actually saved before kickoff. The database keeps production forecast payloads immutable and attaches actual results separately. Multiple pre-kickoff revisions are allowed as separate records; prospective reports evaluate the latest revision per fixture/model.

Changing refit cadence is an experiment on development periods, not a decision to make by inspecting final-season results. Imported historical source corrections cannot recover the original source's truth at every old date. For strict auditability, maintain timestamped historical archives.

Exercise: contrast a model trained once before a test season with one refitted every month. Identify which results each is allowed to observe.
