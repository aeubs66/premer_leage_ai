"""Application workflows used by CLI and API, without dataframe/SQL coupling."""

import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd

from football_ai.config import Settings
from football_ai.data.providers import CSVDataProvider, FootballDataAPIProvider
from football_ai.data.schemas import Observation
from football_ai.data.store import download, download_fixtures, load_snapshot, save_snapshot
from football_ai.database.repository import Repository
from football_ai.evaluation.metrics import metrics
from football_ai.evaluation.reports import write_report
from football_ai.features.pipeline import FeaturePipeline
from football_ai.training.registry import LocalRegistry
from football_ai.training.trainer import feature_frame

log = logging.getLogger(__name__)


def update_data(
    settings: Settings,
    csv_path: Path | None = None,
    season=None,
    fixtures=None,
    api_fixtures=False,
    offline=False,
):
    settings.prepare()
    repository = Repository(settings)
    repository.migrate()
    try:
        previous, _ = load_snapshot(settings)
    except ValueError:
        previous = []
    incoming = (
        CSVDataProvider(csv_path, season).records()
        if csv_path
        else download(settings, refresh=not offline)
    )
    if fixtures:
        incoming += CSVDataProvider(fixtures, season).fixtures()
    elif settings.path(settings.load("data")["fixture_csv"]).exists():
        incoming += CSVDataProvider(
            settings.path(settings.load("data")["fixture_csv"]), season
        ).fixtures()
    elif not csv_path:
        incoming += download_fixtures(settings, offline)
    if api_fixtures:
        token = (
            settings.football_data_token.get_secret_value()
            if settings.football_data_token
            else None
        )
        provider = FootballDataAPIProvider(token)
        incoming += provider.results() + provider.fixtures()
    merged = {m.id: m for m in previous}
    added, changed = 0, 0
    for match in incoming:
        prior = merged.get(match.id)
        if prior is not None and prior.status == "finished" and match.status != "finished":
            continue
        added += prior is None
        changed += prior is not None and prior != match
        # Preserve richer CSV statistics when an API sends a result-only revision.
        if prior is not None and not match.home_stats:
            match = match.model_copy(
                update={"home_stats": prior.home_stats, "away_stats": prior.away_stats}
            )
        merged[match.id] = match
    records = sorted(merged.values(), key=lambda m: (m.kickoff, m.id))
    version = save_snapshot(settings, records)
    repository.sync_matches(records)
    attached_results = repository.record_results()
    frame, feature_version = feature_frame(settings, records, version, repository.observations())
    repository.save_features(records, frame, version, feature_version)
    from football_ai.database.models import data_sources

    with repository.engine.begin() as connection:
        repository.upsert(
            connection,
            data_sources,
            {"id": version},
            {
                "payload": {
                    "sources": sorted({m.source for m in records}),
                    "dataset_version": version,
                }
            },
        )
    summary = {
        "dataset_version": version,
        "records": len(records),
        "attached_results": attached_results,
        "added": added,
        "changed": changed,
        "feature_version": feature_version,
        "seasons": sorted({m.season for m in records}),
    }
    log.info("Updated data: %s", summary)
    return summary


def import_observations(settings, path):
    records = [
        Observation.model_validate_json(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    repository = Repository(settings)
    repository.save_observations(records)
    return {"imported": len(records)}


def upcoming(repository, days=14):
    now = datetime.now(UTC)
    return [
        m
        for m in repository.matches()
        if m.status == "scheduled" and now < m.kickoff <= now + timedelta(days=days)
    ]


def recent_matches(repository, days=30):
    """Keep started fixtures visible; only publish final scores once available."""
    now = datetime.now(UTC)
    links = repository.latest_prediction_ids()
    rows = []
    for match in repository.matches():
        if not now - timedelta(days=days) <= match.kickoff <= now:
            continue
        payload = match.model_dump(mode="json")
        confirmed = match.status == "finished" and match.result_available_at <= now
        if not confirmed:
            payload["home_goals"] = payload["away_goals"] = None
        payload["display_status"] = (
            "finished"
            if confirmed
            else match.status
            if match.status in ("postponed", "cancelled")
            else "awaiting_result"
        )
        payload["prediction_id"] = links.get(match.id)
        rows.append(payload)
    return sorted(rows, key=lambda row: (row["kickoff"], row["id"]), reverse=True)


def team_form(repository, team, limit=20):
    records = repository.matches()
    if team not in {m.home_team for m in records} | {m.away_team for m in records}:
        raise KeyError("Unknown team")
    history = [
        m
        for m in records
        if m.status == "finished"
        and m.result_available_at < datetime.now(UTC)
        and team in (m.home_team, m.away_team)
    ]
    history = sorted(history, key=lambda m: m.kickoff)[-limit:]
    pipeline = FeaturePipeline(repository.settings.load("features"), repository.observations())
    features = pipeline.transform(records)
    rows = []
    for match in history:
        home = match.home_team == team
        stats = match.home_stats if home else match.away_stats
        other = match.away_stats if home else match.home_stats
        goals, conceded = (
            (match.home_goals, match.away_goals) if home else (match.away_goals, match.home_goals)
        )
        rows.append(
            {
                "kickoff": match.kickoff.isoformat(),
                "opponent": match.away_team if home else match.home_team,
                "venue": "home" if home else "away",
                "goals_for": goals,
                "goals_against": conceded,
                "result": "W" if goals > conceded else "D" if goals == conceded else "L",
                "points": 3 if goals > conceded else 1 if goals == conceded else 0,
                "xg": stats.get("xg"),
                "xga": other.get("xg"),
                "elo_before": float(features.loc[match.id, "home_elo" if home else "away_elo"]),
            }
        )
    return {"team": team, "matches": rows}


def evaluate_saved(settings):
    repository = Repository(settings)
    rows = repository.evaluated_predictions()
    if not rows:
        return {"n": 0, "message": "No saved predictions have results yet"}
    # Multiple pre-kickoff forecasts are revisions; evaluate the last per fixture/model.
    latest: dict = {}
    for payload, actual in rows:
        key = (payload["fixture_id"], payload["model_version"])
        if key not in latest or payload["generated_at"] > latest[key][0]["generated_at"]:
            latest[key] = (payload, actual)
    results = {}
    for version in {key[1] for key in latest}:
        subset = [row for key, row in latest.items() if key[1] == version]
        probabilities = [
            [payload["probabilities"][label] for label in ["home", "draw", "away"]]
            for payload, _ in subset
        ]
        results[version] = metrics([actual for _, actual in subset], probabilities)
    settings.path("reports/prospective-performance.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )
    return results


def backtest(settings, version=None):
    artifact, manifest = LocalRegistry(settings).load(version, research=True)
    records, _ = load_snapshot(settings, manifest["dataset_version"])
    observations = Repository(settings).observations()
    test = [m for m in records if m.status == "finished" and m.season == manifest["test_season"]]
    test = sorted(test, key=lambda m: m.kickoff)
    config = artifact.recipe["feature_config"]
    frame = FeaturePipeline(config, observations).transform(records)
    interval = artifact.recipe["training_config"]["backtest_refit_days"]
    refit_at = None
    working = artifact
    rows = []
    for match in test:
        if refit_at is None or (match.kickoff - refit_at).days >= interval:
            eligible = [
                m
                for m in records
                if m.status == "finished" and m.result_available_at < match.kickoff
            ]
            working = artifact.refit(frame.loc[[m.id for m in eligible]], eligible)
            refit_at = match.kickoff
            cutoff = max(m.result_available_at for m in eligible)
        p = working.predict(frame.loc[[match.id]], [match])[0][0]
        rows.append(
            {
                "match_id": match.id,
                "kickoff": match.kickoff.isoformat(),
                "model_version": manifest["version"],
                "training_cutoff": cutoff.isoformat(),
                "home": float(p[0]),
                "draw": float(p[1]),
                "away": float(p[2]),
                "actual": match.outcome,
                "kind": "retrospective_walk_forward",
            }
        )
    predictions = pd.DataFrame(rows)
    result = metrics(predictions.actual, predictions[["home", "draw", "away"]].to_numpy())
    write_report(
        settings.path(f"reports/{manifest['version']}/walk-forward"),
        {
            "validation": result,
            "policy": "Frozen pre-test recipe; chronological monthly refits; final season never selects the recipe",
        },
        predictions,
    )
    return result
