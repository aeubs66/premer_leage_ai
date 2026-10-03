"""Source-independent contracts. Null statistics mean unavailable, never zero."""

import hashlib
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ALIASES = {
    "Man City": "Manchester City", "Man United": "Manchester United",
    "Manchester United FC": "Manchester United", "Manchester City FC": "Manchester City",
    "Tottenham": "Tottenham Hotspur", "Spurs": "Tottenham Hotspur",
    "Wolves": "Wolverhampton Wanderers", "West Ham": "West Ham United",
    "Nott'm Forest": "Nottingham Forest", "Newcastle": "Newcastle United",
    "Brighton": "Brighton & Hove Albion", "Leicester": "Leicester City",
    "Leeds": "Leeds United", "Sheffield United": "Sheffield United",
}


def team_name(value: str) -> str:
    clean = value.strip().removesuffix(" FC").removesuffix(" AFC")
    return ALIASES.get(clean, clean)


def match_key(season: str, home: str, away: str, competition: str = "E0") -> str:
    # League fixture identity deliberately excludes kickoff: postponement keeps its identity.
    return hashlib.sha256(f"{competition}|{season}|{home}|{away}".encode()).hexdigest()[:24]


class Match(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    season: str
    competition: str = "E0"
    kickoff: datetime
    home_team: str
    away_team: str
    status: Literal["scheduled", "finished", "postponed", "cancelled"]
    home_goals: int | None = Field(default=None, ge=0)
    away_goals: int | None = Field(default=None, ge=0)
    available_at: datetime | None = None
    availability_assumed: bool = False
    date_only: bool = False
    home_stats: dict[str, float | None] = Field(default_factory=dict)
    away_stats: dict[str, float | None] = Field(default_factory=dict)
    source: str
    source_id: str | None = None

    @model_validator(mode="after")
    def valid(self) -> "Match":
        if self.home_team == self.away_team:
            raise ValueError("A team cannot play itself")
        if self.kickoff.tzinfo is None or (self.available_at and self.available_at.tzinfo is None):
            raise ValueError("Timestamps must have a timezone")
        self.kickoff = self.kickoff.astimezone(UTC)
        if self.available_at:
            self.available_at = self.available_at.astimezone(UTC)
        if self.status == "finished":
            if self.home_goals is None or self.away_goals is None or self.available_at is None:
                raise ValueError("Finished matches require both goals and availability")
            if self.available_at <= self.kickoff:
                raise ValueError("Result availability must follow kickoff")
        elif self.home_goals is not None or self.away_goals is not None:
            raise ValueError("Unfinished matches cannot have final goals")
        return self

    @property
    def outcome(self) -> int:
        if self.status != "finished":
            raise ValueError("Match has no result")
        assert self.home_goals is not None and self.away_goals is not None
        return 0 if self.home_goals > self.away_goals else 1 if self.home_goals == self.away_goals else 2


class Observation(BaseModel):
    """Optional enrichment usable only after its real publication timestamp."""

    team: str
    player_id: str | None = None
    fixture_id: str | None = None
    kind: Literal["availability", "lineup", "squad", "cup_fixture"]
    observed_at: datetime
    available_at: datetime
    values: dict[str, float | str | None]
    source: str

    @model_validator(mode="after")
    def timed(self) -> "Observation":
        if self.available_at.tzinfo is None or self.observed_at.tzinfo is None:
            raise ValueError("Observations need timezone-aware publication timestamps")
        if self.available_at < self.observed_at:
            raise ValueError("Publication cannot precede observation")
        return self
