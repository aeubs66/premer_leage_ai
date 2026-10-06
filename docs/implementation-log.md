# Implementation log

## Phases 0–1

Inspected the empty destination and local hardware. Selected Python 3.12, uv, SQLite, LIGHT, vendor-independent data contracts, chronological evaluation, and optional CPU PyTorch. Established package/configuration/testing/logging/CLI foundation. No player or xG availability is assumed.

## Phases 2–5

Implemented canonical CSV/API contracts, strict result validation, timezone handling, immutable raw responses and dataset snapshots, corrections, and stable fixture identity. Implemented publication-time feature replay, season tables, recent/venue form, schedule features, optional observations, and Elo. Added probability baselines and regularized Poisson/Dixon–Coles score distributions. Tests caught and fixed zero-scoring-history division and an initial migration foreign-key type omission.

## Phases 6–10

Implemented CPU XGBoost, H2H ablation, bounded serial Optuna searches, compact CPU PyTorch embeddings, calibration alternatives, weighted/logistic/small-meta stacking, and nested chronological evaluation. Real downloads yielded 1,570 records across 2022/2023–2026/2027. The first LIGHT/FAST run completed with all core learners. Selection favored a small meta ensemble with Elo, Poisson, XGBoost, and neural; no calibration transform won validation. The sealed 2025/2026 test had 380 matches: log loss 1.0303, Brier 0.6195, accuracy 47.37%. These metrics did not influence recipe selection. Monthly frozen-recipe walk-forward measured log loss 1.0264 and accuracy 48.16%.

## Phases 11–15

Integrated local MLflow SQLite tracking, checksummed research/production artifacts, SQLAlchemy/Alembic storage, database-level immutable-prediction triggers, result attachment, retraining gates, rollback, API contracts, and the Next.js analytics dashboard. Implemented result/fixture updates, optional enrichment import, prospective evaluation, and monthly historical replay. End-to-end tests train actual models on explicitly synthetic test records and verify prediction saving, exact tree SHAP, probability/score coherence, immutability, result attachment, and evaluation. No synthetic records enter the real database.

## Phases 16–17

Wrote mathematical explanations, Windows commands, limitations, automation instructions, and eleven-level study guide. Python lint/type checks and the frontend production build pass. The frontend dependency audit initially found vulnerable development tooling; replaced that tooling with compatible current versions and verified a clean audit. PostgreSQL tests are conditional because no server/test URL is configured. The published fixture CSV contained no EPL fixtures during verification, so the live dashboard displays the truthful empty state; API and alternate CSV fixtures remain supported.

Final checks, source archive metadata, research reports, and the final Git checkpoint are recorded in the delivery verification document. The final review also repaired delayed-result Elo replay, keyed feature caches to their implementation, limited explanations to selected model components, honored training configuration defaults, and verified secret fixture-token loading from `.env`. No predictive accuracy guarantee is made.

## Forecast page reading order - 2026-10-06

Moved likely scores and expected goals immediately after the outcome probabilities. Saved forecast warnings, coverage and lineage remain visible. Graphs, the full score grid, and model evidence/context now use three native, keyboard-accessible disclosure sections, closed initially. Content mounts when opened so responsive charts measure visible containers and animate on demand; reduced-motion preferences remain respected. Forecast data and model behavior are unchanged.

Verified disclosure opening, closing and reopening with Testing Library; all seven frontend tests, lint, TypeScript and the production build pass. The current saved forecast page and its API returned HTTP 200. Live browser visual inspection remains unavailable because the browser control tool could not initialize.

## Probability provenance explanation - 2026-10-06

Added an expandable explanation directly below forecast probabilities. It displays only the contributing models and their saved outcome probabilities, the final forecast, chronological feature/recipe context, available-data coverage, publication-time assumptions, and saved lineage/cutoff. It explains probability interpretation and shows measured top-outcome calibration evidence only for bins with at least 30 examples. Component feature attributions are explicitly separated from final probability contributions; no model weights or exact additive ensemble explanations are invented. Older snapshots have explicit missing-lineage fallbacks.

All nine frontend tests, lint, type checks and production build passed; the current forecast page returned HTTP 200. Browser visual inspection remains unavailable.
