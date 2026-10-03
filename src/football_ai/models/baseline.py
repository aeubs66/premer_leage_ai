"""Honest reference models: constants, frequencies, and previous-season strength."""

import numpy as np

from football_ai.models.base import normalize


class Baseline:
    def __init__(self, mode="frequency"):
        self.mode = mode

    def fit(self, features, matches):
        counts = np.bincount([m.outcome for m in matches], minlength=3) + 1
        self.frequency = counts / counts.sum()
        self.previous: dict[tuple[str, str], list[float]] = {}
        for match in matches:
            for team, goals, conceded in [
                (match.home_team, match.home_goals, match.away_goals),
                (match.away_team, match.away_goals, match.home_goals),
            ]:
                points = 3 if goals > conceded else 1 if goals == conceded else 0
                self.previous.setdefault((match.season, team), []).append(points)
        return self

    def predict_proba(self, features, matches):
        if self.mode == "home":
            return np.tile([1 - 2e-6, 1e-6, 1e-6], (len(matches), 1))
        probabilities = np.tile(self.frequency, (len(matches), 1))
        if self.mode == "previous_season":
            for i, match in enumerate(matches):
                year = int(match.season[:4]) - 1
                season = f"{year}/{year + 1}"
                home = self.previous.get((season, match.home_team), [])
                away = self.previous.get((season, match.away_team), [])
                hp = (sum(home) + 5 * 1.3) / (len(home) + 5)
                ap = (sum(away) + 5 * 1.3) / (len(away) + 5)
                probabilities[i] *= np.exp([0.5 * (hp - ap), 0, 0.5 * (ap - hp)])
        return normalize(probabilities)
