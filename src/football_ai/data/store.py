"""Immutable content-addressed datasets and auditable downloads."""

import hashlib
import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

from football_ai.config import Settings
from football_ai.data.providers import CSVDataProvider
from football_ai.data.schemas import Match

log = logging.getLogger(__name__)


def validate_records(records: list[Match]) -> list[Match]:
    seen: dict[str, Match] = {}
    for record in records:
        if record.id in seen and seen[record.id] != record:
            raise ValueError(f"Conflicting duplicate match: {record.id}")
        for stats in (record.home_stats, record.away_stats):
            for name, value in stats.items():
                if value is not None and (value < 0 or not float("-inf") < value < float("inf")):
                    raise ValueError(f"Invalid {name}: {value}")
        seen[record.id] = record
    return sorted(seen.values(), key=lambda m: (m.kickoff, m.id))


def save_snapshot(settings: Settings, records: list[Match]) -> str:
    settings.prepare()
    records = validate_records(records)
    payload = "\n".join(m.model_dump_json() for m in records) + "\n"
    digest = hashlib.sha256(payload.encode()).hexdigest()
    target = settings.path(f"data/processed/{digest}.jsonl")
    if not target.exists():
        target.write_text(payload, encoding="utf-8")
    manifest = {"version": digest, "records": len(records), "created_at": datetime.now(UTC).isoformat(),
                "seasons": sorted({m.season for m in records}), "availability_assumptions": "3h after timed kickoff; next local day for date-only CSV"}
    settings.path("data/processed/latest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return digest


def load_snapshot(settings: Settings, version: str | None = None) -> tuple[list[Match], str]:
    if version is None:
        path = settings.path("data/processed/latest.json")
        if not path.exists():
            raise ValueError("No dataset. Run football-ai update-data first.")
        version = json.loads(path.read_text())["version"]
    records = [Match.model_validate_json(line) for line in settings.path(f"data/processed/{version}.jsonl").read_text(encoding="utf-8").splitlines() if line]
    return records, version


def download(settings: Settings, refresh: bool = True) -> list[Match]:
    settings.prepare()
    config = settings.load("data")
    now = datetime.now(UTC)
    latest = now.year if now.month >= 7 else now.year - 1
    records: list[Match] = []
    obtained = 0
    # Search farther back if the current season has not yet been published.
    with httpx.Client(timeout=config["timeout_seconds"], follow_redirects=True) as client:
        for year in range(latest, latest - config["seasons"] - 2, -1):
            code = f"{year % 100:02d}{(year + 1) % 100:02d}"
            url = f"{config['base_url']}/mmz4281/{code}/E0.csv"
            directory = settings.path(f"data/raw/{code}")
            cached = sorted(directory.glob("*.csv")) if directory.exists() else []
            body = None
            if cached and (not refresh or year < latest - 1):
                path = max(cached, key=lambda p: p.stat().st_mtime)
            else:
                for attempt in range(config["retries"]):
                    try:
                        response = client.get(url)
                        if response.status_code == 404:
                            break
                        response.raise_for_status()
                        body = response.content
                        if b"HomeTeam" not in body[:1000]:
                            raise ValueError("Response is not a results CSV")
                        break
                    except (httpx.HTTPError, ValueError) as exc:
                        log.warning("Download %s attempt %s: %s", code, attempt + 1, exc)
                        if attempt + 1 < config["retries"]:
                            time.sleep(2 ** attempt)
                if body:
                    directory.mkdir(parents=True, exist_ok=True)
                    digest = hashlib.sha256(body).hexdigest()
                    path = directory / f"{digest}.csv"
                    if not path.exists():
                        path.write_bytes(body)
                        path.with_suffix(".json").write_text(json.dumps({"url": url, "sha256": digest, "downloaded_at": now.isoformat()}, indent=2), encoding="utf-8")
                elif cached:
                    path = max(cached, key=lambda p: p.stat().st_mtime)
                    log.warning("Using cached season %s", code)
                else:
                    continue
            season_records = CSVDataProvider(path, f"{year}/{year + 1}", config["result_lag_hours"]).records()
            if not season_records:
                continue
            records.extend(season_records)
            obtained += 1
            if obtained >= config["seasons"]:
                break
    if not records:
        raise ValueError("No downloadable seasons or cached data. Use update-data --csv PATH --season YEAR/YEAR.")
    return validate_records(records)
