# Data pipeline

The provider answers: what did a source publish? Validation answers: does that record make sense? Versioning answers: exactly which input did this experiment use?

Read `data/schemas.py`, `data/providers.py`, `data/store.py`, and `services.py` under the Python package. Providers emit `Match` or timestamped `Observation` records. Vendor fields never reach models directly. The downloader stores each response under its SHA-256 hash, with URL and retrieval time. Normalized JSON Lines snapshots are also content addressed. `latest.json` is a pointer; old snapshots are preserved.

Fixture identity is competition + season + home + away, independent of date. Postponements can change kickoff without introducing a duplicate. This identity is designed for a double round-robin league, not knockout tournaments. Corrections create a new snapshot; old evaluations remain reproducible from their snapshot. Previously unavailable results become usable only after their availability cutoff.

## CSV contracts

Football-Data columns: `Date`, optional `Time`, `HomeTeam`, `AwayTeam`, `FTHG`, `FTAG`; match statistics are explicitly mapped. `Div` must be `E0` when supplied. Dates are UK-local, converted using Europe/London including daylight saving. No odds columns are admitted.

Canonical CSV: `season,home_team,away_team,kickoff,status,home_goals,away_goals,available_at`. Use ISO timezone-aware timestamps and leave goals blank for scheduled fixtures. Optional statistics use `HS,AS,HST,AST,HC,AC,HF,AF,HY,AY,HR,AR,HxG,AxG,HPoss,APoss`. A confirmed kickoff time is required to save a production forecast.

Optional observations are JSON Lines conforming to `Observation`. Include team, fixture_id, optional player_id, kind, observed_at, available_at, source, and values. Import with `football-ai import-observations PATH`. Missing-player contribution values must come from historical evidence, not subjective fame. A cup fixture observation contributes only if its event and publication both precede the feature cutoff.

Historical availability in plain result CSVs is assumed: three hours after a timed kickoff, or the next local day for a date-only record. This is a documented approximation, not evidence of original publication time. Timestamped archives are required for rigorous enrichment backtests.
