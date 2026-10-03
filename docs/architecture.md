# Architecture and implementation decisions

The specification is preserved in `project-specification.txt`. This is a forecasting and learning platform, not a betting tool. Results must be measured rather than promised.

## Components and data flow

Provider → raw immutable cache → validated canonical records → versioned dataset → historical feature replay → chronological training/evaluation → versioned artifact → inference → append-only prediction storage → FastAPI → Next.js.

Providers own vendor mappings. Repositories own SQL. Features own temporal state. Models consume explicit numeric matrices and canonical match metadata; they never query current database tables during training. The API and CLI call the same services.

SQLite is the local default. PostgreSQL uses the same SQLAlchemy models and migrations. No Docker, cloud account, or GPU is required. Optional dependency groups keep PyTorch, MLflow, SHAP, and PostgreSQL separate.

## Time boundaries

Feature cutoffs are UTC. A result is usable only once its availability timestamp precedes the cutoff. Historical availability assumptions must be declared; date-only records are usable the next day. Fixtures with the same timestamp see the same prior state. Player observations without historical publication times cannot be used in backtests. Production prediction records and result attachments are separate.

## Evaluation boundaries

The latest complete season is sealed as the final test. Earlier data supplies nested chronological evaluation. Base-model training, meta-model fitting, calibration, and candidate selection use separate temporal blocks. Final-test reports never select deployment recipes. Current-season forecasts are prospective records.

## CPU budget and delivery

LIGHT uses two threads and serial tuning. Small data supports statistical models, histogram trees, and compact embeddings. Transformers and graph networks require a documented experiment hypothesis; they are not production defaults.

Follow phases 0–17 from the specification. At each boundary run relevant tests, document decisions, review leakage, and commit the passing state. Risks include sparse validation data, missing advanced statistics, provider interruptions, retrospective corrections, and calibration instability. None are handled by inventing data or reporting fictional accuracy.
