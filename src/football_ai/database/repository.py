"""Transactional SQL operations, portable to SQLite and PostgreSQL."""

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

import numpy as np
from sqlalchemy import create_engine, delete, event, insert, select, update
from sqlalchemy.orm import Session

from football_ai.config import Settings
from football_ai.data.schemas import Match, Observation
from football_ai.database import models as db


class Repository:
    def __init__(self, settings: Settings):
        settings.prepare()
        self.settings = settings
        self.engine = create_engine(settings.db_url())
        if self.engine.dialect.name == "sqlite":

            @event.listens_for(self.engine, "connect")
            def configure_sqlite(connection, _):
                connection.execute("PRAGMA foreign_keys=ON")
                connection.execute("PRAGMA busy_timeout=5000")

    def migrate(self):
        from alembic import command
        from alembic.config import Config

        config = Config(str(self.settings.path("alembic.ini")))
        config.set_main_option(
            "script_location", str(self.settings.path("src/football_ai/database/migrations"))
        )
        config.set_main_option("sqlalchemy.url", self.settings.db_url().replace("%", "%%"))
        command.upgrade(config, "head")

    @staticmethod
    def upsert(connection, table, keys, values):
        condition = [table.c[name] == value for name, value in keys.items()]
        exists = connection.execute(select(table).where(*condition)).first()
        if exists and values:
            connection.execute(update(table).where(*condition).values(**values))
        elif not exists:
            connection.execute(insert(table).values(**keys, **values))

    def sync_matches(self, records: list[Match]):
        self.migrate()
        with self.engine.begin() as connection:
            for match in records:
                for name in [match.home_team, match.away_team]:
                    self.upsert(connection, db.teams, {"name": name}, {})
                payload = match.model_dump(mode="json")
                self.upsert(
                    connection,
                    db.matches,
                    {"id": match.id},
                    {
                        "season": match.season,
                        "kickoff": match.kickoff,
                        "status": match.status,
                        "payload": payload,
                    },
                )
                if match.status != "finished":
                    self.upsert(
                        connection,
                        db.fixtures,
                        {"id": match.id},
                        {"kickoff": match.kickoff, "payload": payload},
                    )
                else:
                    connection.execute(delete(db.fixtures).where(db.fixtures.c.id == match.id))
                    for team, stats in [
                        (match.home_team, match.home_stats),
                        (match.away_team, match.away_stats),
                    ]:
                        self.upsert(
                            connection,
                            db.team_match_stats,
                            {"match_id": match.id, "team": team},
                            {"payload": stats},
                        )

    def matches(self) -> list[Match]:
        with self.engine.connect() as connection:
            rows: list = list(
                connection.execute(select(db.matches.c.payload).order_by(db.matches.c.kickoff))
                .scalars()
                .all()
            )
        return [Match.model_validate(row) for row in rows]

    def save_observations(self, records: list[Observation]):
        self.migrate()
        with self.engine.begin() as connection:
            for record in records:
                payload = record.model_dump(mode="json")
                identifier = hashlib.sha256(
                    json.dumps(payload, sort_keys=True).encode()
                ).hexdigest()
                self.upsert(connection, db.teams, {"name": record.team}, {})
                self.upsert(
                    connection,
                    db.observations,
                    {"id": identifier},
                    {"available_at": record.available_at, "payload": payload},
                )
                if record.kind == "availability":
                    self.upsert(
                        connection,
                        db.injuries,
                        {"id": identifier},
                        {
                            "team": record.team,
                            "available_at": record.available_at,
                            "payload": payload,
                        },
                    )
                if record.player_id:
                    self.upsert(
                        connection,
                        db.players,
                        {"id": record.player_id},
                        {
                            "team": record.team,
                            "payload": {"id": record.player_id, "source": record.source},
                        },
                    )

    def observations(self) -> list[Observation]:
        with self.engine.connect() as connection:
            rows: list[dict[str, Any]] = list(
                connection.execute(select(db.observations.c.payload)).scalars()
            )
            return [Observation.model_validate(row) for row in rows]

    def save_features(self, records, frame, dataset_version, feature_version):
        with self.engine.begin() as connection:
            for match in records:
                row: Any = frame.loc[match.id]
                payload = {
                    name: float(value) if np.isfinite(value) else None
                    for name, value in row.items()
                }
                self.upsert(
                    connection,
                    db.features,
                    {
                        "match_id": match.id,
                        "dataset_version": dataset_version,
                        "feature_version": feature_version,
                    },
                    {"cutoff": match.kickoff, "payload": payload},
                )
                for side, team in [("home", match.home_team), ("away", match.away_team)]:
                    self.upsert(
                        connection,
                        db.elo_history,
                        {"match_id": match.id, "team": team, "feature_version": feature_version},
                        {"rating": payload[f"{side}_elo"]},
                    )

    def save_model(self, manifest):
        self.migrate()
        with self.engine.begin() as connection:
            self.upsert(
                connection,
                db.model_versions,
                {"version": manifest["version"]},
                {"trained_at": datetime.fromisoformat(manifest["trained_at"]), "payload": manifest},
            )
            self.upsert(
                connection, db.experiments, {"id": manifest["version"]}, {"payload": manifest}
            )

    def save_prediction(self, payload, fixture):
        now = datetime.fromisoformat(payload["generated_at"])
        if (
            now >= fixture.kickoff
            or datetime.now(UTC) >= fixture.kickoff
            or fixture.status != "scheduled"
        ):
            raise ValueError("Predictions must be saved before scheduled kickoff")
        with Session(self.engine) as session:
            session.add(
                db.Prediction(
                    id=payload["prediction_id"],
                    match_id=fixture.id,
                    model_version=payload["model_version"],
                    generated_at=now,
                    kickoff=fixture.kickoff,
                    payload=payload,
                )
            )
            session.commit()

    def prediction(self, identifier: str) -> dict[str, Any] | None:
        with Session(self.engine) as session:
            row = session.get(db.Prediction, identifier)
            if row is None:
                return None
            payload = dict(row.payload)
            result = session.execute(
                select(db.prediction_results.c.payload).where(
                    db.prediction_results.c.prediction_id == identifier
                )
            ).scalar_one_or_none()
            payload["result"] = result
            return payload

    def latest_prediction_ids(self) -> dict[str, str]:
        """Link match cards to saved forecasts without creating post-kickoff predictions."""
        with self.engine.connect() as connection:
            rows = connection.execute(
                select(db.Prediction.match_id, db.Prediction.id).order_by(
                    db.Prediction.generated_at, db.Prediction.id
                )
            )
            return {match_id: identifier for match_id, identifier in rows}

    def record_results(self):
        count = 0
        actuals = {
            m.id: m
            for m in self.matches()
            if m.status == "finished" and m.result_available_at <= datetime.now(UTC)
        }
        with self.engine.begin() as connection:
            saved: Any = connection.execute(
                select(db.Prediction.id, db.Prediction.match_id, db.Prediction.payload)
            ).all()
            for identifier, match_id, payload in saved:
                if match_id not in actuals:
                    continue
                match = actuals[match_id]
                probability = payload["probabilities"][["home", "draw", "away"][match.outcome]]
                result = {
                    "actual": match.outcome,
                    "home_goals": match.home_goals,
                    "away_goals": match.away_goals,
                    "log_loss": float(-np.log(max(probability, 1e-12))),
                }
                self.upsert(
                    connection,
                    db.prediction_results,
                    {"prediction_id": identifier},
                    {"actual": match.outcome, "recorded_at": datetime.now(UTC), "payload": result},
                )
                count += 1
        return count

    def evaluated_predictions(self):
        with self.engine.connect() as connection:
            query = select(db.Prediction.payload, db.prediction_results.c.actual).join(
                db.prediction_results, db.prediction_results.c.prediction_id == db.Prediction.id
            )
            return connection.execute(query).all()

    def model_manifests(self):
        with self.engine.connect() as connection:
            return list(
                connection.execute(
                    select(db.model_versions.c.payload).order_by(
                        db.model_versions.c.trained_at.desc()
                    )
                ).scalars()
            )
