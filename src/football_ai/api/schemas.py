"""Documented request and response contracts for the analytics UI."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator


class PredictRequest(BaseModel):
    fixture_id: str | None = Field(default=None, max_length=64)
    home_team: str | None = Field(default=None, min_length=1, max_length=120)
    away_team: str | None = Field(default=None, min_length=1, max_length=120)
    match_date: date | None = None

    @model_validator(mode="after")
    def valid_fixture_request(self):
        if not self.fixture_id and not (self.home_team and self.away_team and self.match_date):
            raise ValueError("Provide fixture_id, or both teams and match_date")
        if self.home_team and self.home_team == self.away_team:
            raise ValueError("Teams must differ")
        return self


class Probabilities(BaseModel):
    home: float = Field(ge=0, le=1)
    draw: float = Field(ge=0, le=1)
    away: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def normalized(self):
        if abs(self.home + self.draw + self.away - 1) > 1e-8:
            raise ValueError("Probabilities must sum to one")
        return self


class ScoreProbability(BaseModel):
    score: str
    probability: float = Field(ge=0, le=1)


class PredictionResponse(BaseModel):
    prediction_id: str
    fixture_id: str
    match: dict[str, str]
    probabilities: Probabilities
    predicted_winner: str
    predicted_score: str
    expected_goals: dict[str, float]
    score_probabilities: list[ScoreProbability]
    score_matrix: list[list[float]]
    other_scores_probability: float
    score_distribution_method: str
    model_predictions: dict[str, Probabilities]
    ensemble_members: list[str]
    model_disagreement: str
    uncertainty: dict[str, Any]
    context: dict[str, Any]
    explanation: dict[str, Any]
    data_coverage: dict[str, Any]
    model_version: str
    dataset_version: str
    feature_version: str
    generated_at: datetime
    features_as_of: datetime
    warning: str
    result: dict[str, Any] | None = None
