"""Portable SQL tables. Prediction payloads are immutable research records."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    event,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


teams = Table("teams", Base.metadata, Column("name", String(120), primary_key=True))
players = Table(
    "players",
    Base.metadata,
    Column("id", String(120), primary_key=True),
    Column("team", ForeignKey("teams.name")),
    Column("payload", JSON, nullable=False),
)
matches = Table(
    "matches",
    Base.metadata,
    Column("id", String(64), primary_key=True),
    Column("season", String(16), index=True),
    Column("kickoff", DateTime(timezone=True), index=True),
    Column("status", String(20)),
    Column("payload", JSON, nullable=False),
)
fixtures = Table(
    "fixtures",
    Base.metadata,
    Column("id", ForeignKey("matches.id"), primary_key=True),
    Column("kickoff", DateTime(timezone=True), index=True),
    Column("payload", JSON, nullable=False),
)
team_match_stats = Table(
    "team_match_stats",
    Base.metadata,
    Column("match_id", ForeignKey("matches.id"), primary_key=True),
    Column("team", ForeignKey("teams.name"), primary_key=True),
    Column("payload", JSON, nullable=False),
)
player_match_stats = Table(
    "player_match_stats",
    Base.metadata,
    Column("match_id", ForeignKey("matches.id"), primary_key=True),
    Column("player_id", ForeignKey("players.id"), primary_key=True),
    Column("payload", JSON, nullable=False),
)
injuries = Table(
    "injuries",
    Base.metadata,
    Column("id", String(64), primary_key=True),
    Column("team", ForeignKey("teams.name")),
    Column("available_at", DateTime(timezone=True), nullable=False),
    Column("payload", JSON, nullable=False),
)
observations = Table(
    "observations",
    Base.metadata,
    Column("id", String(64), primary_key=True),
    Column("available_at", DateTime(timezone=True), nullable=False),
    Column("payload", JSON, nullable=False),
)
elo_history = Table(
    "elo_history",
    Base.metadata,
    Column("match_id", ForeignKey("matches.id"), primary_key=True),
    Column("team", ForeignKey("teams.name"), primary_key=True),
    Column("feature_version", String(64), primary_key=True),
    Column("rating", Float, nullable=False),
)
features = Table(
    "features",
    Base.metadata,
    Column("match_id", ForeignKey("matches.id"), primary_key=True),
    Column("dataset_version", String(64), primary_key=True),
    Column("feature_version", String(64), primary_key=True),
    Column("cutoff", DateTime(timezone=True)),
    Column("payload", JSON, nullable=False),
)
model_versions = Table(
    "model_versions",
    Base.metadata,
    Column("version", String(64), primary_key=True),
    Column("trained_at", DateTime(timezone=True), nullable=False),
    Column("payload", JSON, nullable=False),
)
experiments = Table(
    "experiments",
    Base.metadata,
    Column("id", String(64), primary_key=True),
    Column("payload", JSON, nullable=False),
)
data_sources = Table(
    "data_sources",
    Base.metadata,
    Column("id", String(64), primary_key=True),
    Column("payload", JSON, nullable=False),
)


class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = (CheckConstraint("generated_at < kickoff", name="ck_prediction_pre_kickoff"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    match_id: Mapped[str] = mapped_column(ForeignKey("matches.id"), nullable=False, index=True)
    model_version: Mapped[str] = mapped_column(ForeignKey("model_versions.version"), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    kickoff: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


prediction_results = Table(
    "prediction_results",
    Base.metadata,
    Column("prediction_id", ForeignKey("predictions.id"), primary_key=True),
    Column("actual", Integer, nullable=False),
    Column("recorded_at", DateTime(timezone=True), nullable=False),
    Column("payload", JSON, nullable=False),
)


@event.listens_for(Prediction, "before_update")
@event.listens_for(Prediction, "before_delete")
def prohibit_prediction_mutation(mapper, connection, target):
    raise ValueError("Saved predictions are immutable; create a new pre-kickoff record")
