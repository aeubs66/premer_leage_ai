"""Educational football Elo: a scalar rating updated against expected results."""

import math


class Elo:
    def __init__(
        self, initial=1500.0, k=20.0, home_advantage=65.0, season_retention=0.75, goal_margin=False
    ):
        self.initial, self.k, self.home_advantage = initial, k, home_advantage
        self.retention, self.goal_margin = season_retention, goal_margin
        self.ratings: dict[str, float] = {}
        self.seasons: dict[str, str] = {}

    def rating(self, team: str, season: str) -> float:
        rating = self.ratings.get(team, self.initial)
        previous = self.seasons.get(team, season)
        if previous != season:
            gaps = max(1, int(season[:4]) - int(previous[:4]))
            rating = self.initial + self.retention**gaps * (rating - self.initial)
        return rating

    def expected(self, home: str, away: str, season: str) -> float:
        difference = self.rating(home, season) + self.home_advantage - self.rating(away, season)
        return 1 / (1 + 10 ** (-difference / 400))

    def update(self, home: str, away: str, season: str, home_goals: int, away_goals: int) -> None:
        expected = self.expected(home, away, season)
        actual = 1.0 if home_goals > away_goals else 0.5 if home_goals == away_goals else 0.0
        multiplier = (
            math.log1p(abs(home_goals - away_goals))
            if self.goal_margin and home_goals != away_goals
            else 1.0
        )
        change = self.k * multiplier * (actual - expected)
        self.ratings[home] = self.rating(home, season) + change
        self.ratings[away] = self.rating(away, season) - change
        self.seasons[home] = self.seasons[away] = season
