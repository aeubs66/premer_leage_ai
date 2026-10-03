"""One replay engine shared by historical training and live predictions.

Results enter state by publication time, not merely by kickoff time. Reading all
fixtures at an identical cutoff therefore cannot expose another fixture's result.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd

from football_ai.data.schemas import Match, Observation
from football_ai.features.elo import Elo

METRICS = ["points", "win", "draw", "loss", "gf", "ga", "gd", "clean_sheet",
           "xg", "xga", "shots", "shots_on_target", "possession", "corners", "fouls", "yellow_cards", "red_cards"]
PLAYER_METRICS = ["unavailable_players", "missing_minutes", "missing_xg", "missing_xa", "missing_defensive_contribution", "missing_goalkeeper"]


class FeatureState:
    def __init__(self, config: dict, observations: list[Observation] | None = None):
        self.config = config
        self.elo = Elo(**config["elo"])
        self.history: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.encounters: dict[tuple[str, str], list[tuple]] = defaultdict(list)
        self.observations = observations or []

    def apply(self, match: Match) -> None:
        assert match.home_goals is not None and match.away_goals is not None
        self.elo.update(match.home_team, match.away_team, match.season, match.home_goals, match.away_goals)
        for team, opponent, gf, ga, venue, stats, other in [
            (match.home_team, match.away_team, match.home_goals, match.away_goals, "home", match.home_stats, match.away_stats),
            (match.away_team, match.home_team, match.away_goals, match.home_goals, "away", match.away_stats, match.home_stats),
        ]:
            win, draw, loss = int(gf > ga), int(gf == ga), int(gf < ga)
            self.history[team].append({"kickoff": match.kickoff, "season": match.season, "opponent": opponent, "venue": venue,
                                       "points": 3 * win + draw, "win": win, "draw": draw, "loss": loss,
                                       "gf": gf, "ga": ga, "gd": gf - ga, "clean_sheet": int(ga == 0),
                                       **stats, "xga": other.get("xg")})
        self.encounters[tuple(sorted([match.home_team, match.away_team]))].append((match.home_team, match.home_goals, match.away_goals))

    @staticmethod
    def mean(records: list[dict], key: str) -> float:
        values = [r[key] for r in records if r.get(key) is not None]
        return float(np.mean(values)) if values else np.nan

    def table(self, season: str) -> dict[str, tuple[int, int, int, int]]:
        totals = {}
        for team, history in self.history.items():
            rows = [r for r in history if r["season"] == season]
            totals[team] = (sum(r["points"] for r in rows), sum(r["gd"] for r in rows), sum(r["gf"] for r in rows), len(rows))
        ranks = {}
        for team, value in totals.items():
            ranks[team] = (1 + sum(other[:3] > value[:3] for other in totals.values()), value[0], value[1], value[3])
        return ranks

    def features(self, fixture: Match, cutoff: datetime | None = None) -> dict[str, float]:
        cutoff = cutoff or fixture.kickoff
        output = {}
        standings = self.table(fixture.season)
        league = [r for rows in self.history.values() for r in rows if r["season"] == fixture.season]
        league_gf = self.mean(league, "gf")
        for side, team, venue in [("home", fixture.home_team, "home"), ("away", fixture.away_team, "away")]:
            # State is already time filtered; a fixture's own stats are never inspected here.
            history = sorted(self.history[team], key=lambda r: r["kickoff"])
            output[f"{side}_elo"] = self.elo.rating(team, fixture.season)
            output[f"{side}_history_count"] = len(history)
            for window in self.config["windows"]:
                for metric in METRICS:
                    output[f"{side}_{metric}_{window}"] = self.mean(history[-window:], metric)
            venue_history = [r for r in history if r["venue"] == venue]
            for metric in METRICS:
                output[f"{side}_venue_{metric}_5"] = self.mean(venue_history[-5:], metric)
            for metric in ["points", "gf", "ga", "xg", "xga"]:
                values = pd.Series([r.get(metric) for r in history], dtype=float)
                output[f"{side}_{metric}_ewm"] = float(values.ewm(alpha=self.config["ewm_alpha"], adjust=False).mean().iloc[-1]) if len(values) else np.nan
            output[f"{side}_rest_days"] = min(60.0, (cutoff - history[-1]["kickoff"]).total_seconds() / 86400) if history else np.nan
            cup = [o for o in self.observations if o.team == team and o.kind == "cup_fixture" and o.available_at < cutoff and o.observed_at < cutoff]
            for days in [7, 14]:
                output[f"{side}_matches_{days}d"] = sum(cutoff - timedelta(days=days) <= r["kickoff"] < cutoff for r in history) + sum(cutoff - timedelta(days=days) <= o.observed_at < cutoff for o in cup)
            position, points, gd, played = standings.get(team, (1 + sum(v[1] > 0 for v in standings.values()), 0, 0, 0))
            output.update({f"{side}_position": position, f"{side}_season_points": points,
                           f"{side}_season_gd": gd, f"{side}_season_played": played,
                           f"{side}_season_progress": played / 38})
            for key, metric in [("attack_strength", "gf"), ("defence_strength", "ga")]:
                # Shrink sparse recent histories to a historical league mean, not a final-season mean.
                rows = history[-10:]
                prior = max(0.1, league_gf) if np.isfinite(league_gf) else 1.3
                output[f"{side}_{key}"] = (sum(r[metric] for r in rows) + 5 * prior) / (len(rows) + 5) / prior
            recent = [o for o in self.observations if o.team == team and o.available_at < cutoff and o.kind in ("availability", "lineup", "squad") and o.fixture_id == fixture.id]
            latest: dict[tuple, Observation] = {}
            for observation in sorted(recent, key=lambda o: o.available_at):
                latest[(observation.kind, observation.player_id)] = observation
            for metric in PLAYER_METRICS:
                values = [o.values.get(metric) for o in latest.values() if isinstance(o.values.get(metric), (int, float))]
                output[f"{side}_{metric}"] = float(sum(values)) if values else np.nan
            output[f"{side}_player_data_available"] = float(bool(recent))
        output["elo_difference"] = output["home_elo"] - output["away_elo"]
        for metric in ["points", "gf", "ga", "xg", "xga"]:
            output[f"difference_{metric}_5"] = output[f"home_{metric}_5"] - output[f"away_{metric}_5"]
        if self.config.get("head_to_head"):
            encounters = self.encounters[tuple(sorted([fixture.home_team, fixture.away_team]))][-5:]
            points = []
            for home, hg, ag in encounters:
                gf, ga = (hg, ag) if home == fixture.home_team else (ag, hg)
                points.append(3 if gf > ga else 1 if gf == ga else 0)
            output["head_to_head_points"] = float(np.mean(points)) if points else np.nan
        return output


class FeaturePipeline:
    def __init__(self, config: dict, observations: list[Observation] | None = None):
        self.config, self.observations = config, observations

    def transform(self, records: list[Match]) -> pd.DataFrame:
        fixtures = sorted(records, key=lambda m: (m.kickoff, m.id))
        results = sorted([m for m in records if m.status == "finished"], key=lambda m: (m.available_at, m.id))
        state = FeatureState(self.config, self.observations)
        pointer = 0
        rows = []
        for fixture in fixtures:
            while pointer < len(results) and results[pointer].available_at < fixture.kickoff:
                state.apply(results[pointer])
                pointer += 1
            rows.append({"match_id": fixture.id, **state.features(fixture)})
        return pd.DataFrame(rows).set_index("match_id")

    def for_fixture(self, results: list[Match], fixture: Match, cutoff: datetime | None = None) -> pd.DataFrame:
        cutoff = cutoff or fixture.kickoff
        state = FeatureState(self.config, self.observations)
        eligible = [m for m in results if m.status == "finished" and m.available_at < cutoff]
        for match in sorted(eligible, key=lambda m: (m.available_at, m.id)):
            state.apply(match)
        return pd.DataFrame([state.features(fixture, cutoff)], index=[fixture.id])
