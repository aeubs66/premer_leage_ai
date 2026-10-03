# Study guide: intuition before equations

All code paths below are relative to `src/football_ai`. Read one level, answer the questions, then make the small exercise in a separate branch. Keep the sealed test untouched.

| Level | Files to read | Concepts | Questions to answer | Exercise |
|---|---|---|---|---|
| 1. Match representation | `data/schemas.py`, `data/providers.py` | Records, labels, timezones, nulls, adapters | What distinguishes a fixture from a result? Why is missing xG not zero? | Import a two-row CSV and inspect canonical timestamps. |
| 2. Historical features | `features/pipeline.py`, `docs/features.md` | Rolling means, weighting, state replay | Which observations exist at kickoff? Why do simultaneous fixtures share prior state? | Hand-calculate last-three points and compare to a test. |
| 3. Elo | `features/elo.py`, `models/elo.py` | Expected result, update, logistic functions | Why do surprising wins move ratings more? How are draws mapped? | Calculate a rating update by hand. |
| 4. Poisson | `models/poisson.py`, `docs/poisson.md` | Distributions, likelihood, independence, expectation | What does lambda mean? Why can score and winner modes differ? | Sum score regions and verify normalization. |
| 5. Evaluation boundaries | `training/splits.py`, `tests/test_features.py` | Chronology, publication time, leakage | Why not random splits? When does a result become available? | Delay a publication and verify feature exclusion. |
| 6. Boosting | `models/boosting.py`, `training/tuning.py` | Trees, regularization, preprocessing, search | Why fit imputation inside a fold? What can depth overfit? | Compare bounded depths on development folds. |
| 7. Neural networks | `models/neural.py`, `docs/neural-network.md` | Vectors, matrices, embeddings, logits, gradients | What are the tensor shapes? What does backpropagation update? | Trace one batch through every layer. |
| 8. Calibration | `models/calibration.py`, `evaluation/metrics.py` | Proper scores, reliability, temperature | Can accuracy stay unchanged while probability quality improves? | Plot a deliberately overconfident development forecast. |
| 9. Ensembles | `models/ensemble.py`, `training/trainer.py` | OOF matrices, constrained optimization, stacking | Why can't the stacker use training predictions? | Compare equal and learned weights on a fresh development block. |
| 10. Backtesting | `services.py`, `docs/backtesting.md` | Refits, lineage, prospective records | How is replay different from a real saved forecast? | Inspect one prediction's training cutoff and data version. |
| 11. Platform engineering | `database/repository.py`, `api/main.py`, `cli.py` | Transactions, schemas, immutable records, injection | Why store results separately? What is the registry responsible for? | Follow one request from API input to saved record. |

Learn linear algebra gradually: a scalar is one value; a vector is a list of numeric coordinates; a matrix arranges rows and columns; a dot product multiplies corresponding coordinates and sums them. In this project, rows are matches and columns are features. Learn how matrix multiplication changes shapes before studying gradient equations.

Negative results are useful. Record your hypothesis before experimenting and distinguish development metrics from independent test evidence.
