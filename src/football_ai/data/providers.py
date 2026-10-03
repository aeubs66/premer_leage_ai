"""CSV and API adapters; vendor fields stop at this boundary."""

import csv
import io
import logging
import os
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Protocol
from zoneinfo import ZoneInfo

import httpx

from football_ai.data.schemas import Match, Observation, match_key, team_name

log = logging.getLogger(__name__)
STATS = {
    "shots": ("HS", "AS"),
    "shots_on_target": ("HST", "AST"),
    "corners": ("HC", "AC"),
    "fouls": ("HF", "AF"),
    "yellow_cards": ("HY", "AY"),
    "red_cards": ("HR", "AR"),
    "xg": ("HxG", "AxG"),
    "possession": ("HPoss", "APoss"),
}


class DataProvider(Protocol):
    def results(self) -> list[Match]: ...
    def fixtures(self) -> list[Match]: ...
    def observations(self) -> list[Observation]: ...


class CSVDataProvider:
    def __init__(self, path: Path, season: str | None = None, lag_hours: int = 3):
        self.path, self.season, self.lag_hours = path, season, lag_hours

    def records(self) -> list[Match]:
        text = self.path.read_text(encoding="utf-8-sig")
        # Canonical CSV contains JSON stats only through separate enrichment files.
        rows = csv.DictReader(io.StringIO(text))
        matches: list[Match] = []
        for line, row in enumerate(rows, 2):
            if not any(row.values()):
                continue
            if row.get("Div") not in (None, "", "E0"):
                continue
            try:
                matches.append(self._parse(row))
            except (ValueError, TypeError, KeyError) as exc:
                raise ValueError(f"{self.path.name}:{line}: {exc}") from exc
        return matches

    def _parse(self, row: dict) -> Match:
        home = team_name(row.get("home_team") or row["HomeTeam"])
        away = team_name(row.get("away_team") or row["AwayTeam"])
        if row.get("kickoff"):
            kickoff = datetime.fromisoformat(row["kickoff"].replace("Z", "+00:00"))
            date_only = False
        else:
            date_text = row["Date"]
            pattern = "%d/%m/%Y" if len(date_text.split("/")[-1]) == 4 else "%d/%m/%y"
            day = datetime.strptime(date_text, pattern)
            date_only = not bool(row.get("Time"))
            hour, minute = map(int, (row.get("Time") or "00:00").split(":"))
            kickoff = day.replace(hour=hour, minute=minute, tzinfo=ZoneInfo("Europe/London"))
        season = row.get("season") or self.season
        if not season:
            start = kickoff.year if kickoff.month >= 7 else kickoff.year - 1
            season = f"{start}/{start + 1}"
        hg = row.get("home_goals", row.get("FTHG"))
        ag = row.get("away_goals", row.get("FTAG"))
        hg = int(str(hg)) if hg not in (None, "") else None
        ag = int(str(ag)) if ag not in (None, "") else None
        available = row.get("available_at")
        availability = (
            datetime.fromisoformat(available.replace("Z", "+00:00")) if available else None
        )
        if hg is not None and availability is None:
            availability = kickoff + (
                timedelta(days=1) if date_only else timedelta(hours=self.lag_hours)
            )
        hs, ast = {}, {}
        for name, (hcol, acol) in STATS.items():
            hs[name] = float(row[hcol]) if row.get(hcol) else None
            ast[name] = float(row[acol]) if row.get(acol) else None
        # Odds and unrecognized columns are never passed through to features.
        return Match(
            id=match_key(season, home, away),
            season=season,
            kickoff=kickoff,
            home_team=home,
            away_team=away,
            status=row.get("status") or ("finished" if hg is not None else "scheduled"),
            home_goals=hg,
            away_goals=ag,
            available_at=availability,
            availability_assumed=bool(hg is not None and not available),
            date_only=date_only,
            home_stats=hs,
            away_stats=ast,
            source="csv",
            source_id=row.get("source_id"),
        )

    def results(self) -> list[Match]:
        return [m for m in self.records() if m.status == "finished"]

    def fixtures(self) -> list[Match]:
        return [m for m in self.records() if m.status != "finished"]

    def observations(self) -> list[Observation]:
        return []


class FootballDataAPIProvider:
    """Optional football-data.org v4 fixture/results adapter with bounded retries."""

    def __init__(self, token: str | None = None):
        self.token = token or os.getenv("FOOTBALL_DATA_TOKEN")
        if not self.token:
            raise ValueError("Set FOOTBALL_DATA_TOKEN or import a fixture CSV")

    def _fetch(self, status: str) -> list[Match]:
        assert self.token is not None
        with httpx.Client(timeout=30, headers={"X-Auth-Token": self.token}) as client:
            response = client.get(
                "https://api.football-data.org/v4/competitions/PL/matches",
                params={"status": status},
            )
            if response.status_code == 429:
                delay = min(60, int(response.headers.get("Retry-After", "6")))
                time.sleep(delay)
                response = client.get(
                    "https://api.football-data.org/v4/competitions/PL/matches",
                    params={"status": status},
                )
            response.raise_for_status()
            records = response.json()["matches"]
        result = []
        for row in records:
            kickoff = datetime.fromisoformat(row["utcDate"].replace("Z", "+00:00"))
            year = int(row["season"]["startDate"][:4])
            season = f"{year}/{year + 1}"
            home, away = team_name(row["homeTeam"]["name"]), team_name(row["awayTeam"]["name"])
            finished = row["status"] == "FINISHED"
            goals = row["score"]["fullTime"]
            result.append(
                Match(
                    id=match_key(season, home, away),
                    season=season,
                    kickoff=kickoff,
                    home_team=home,
                    away_team=away,
                    status="finished" if finished else "scheduled",
                    home_goals=goals["home"] if finished else None,
                    away_goals=goals["away"] if finished else None,
                    available_at=datetime.now(UTC) if finished else None,
                    source="football-data.org",
                    source_id=str(row["id"]),
                )
            )
        return result

    def results(self) -> list[Match]:
        return self._fetch("FINISHED")

    def fixtures(self) -> list[Match]:
        return self._fetch("SCHEDULED,TIMED")

    def observations(self) -> list[Observation]:
        return []
