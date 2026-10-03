import os
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import inspect
from sqlalchemy.orm import Session
from test_data import match

from football_ai.config import Settings
from football_ai.database.models import Prediction
from football_ai.database.repository import Repository


@pytest.fixture
def repository(tmp_path):
    settings = Settings(
        root=Settings().root, database_url="sqlite:///" + (tmp_path / "test.db").as_posix()
    )
    repository = Repository(settings)
    repository.migrate()
    return repository


def test_migrations_idempotency_and_corrections(repository):
    first = match()
    repository.sync_matches([first, first])
    assert len(repository.matches()) == 1
    repository.sync_matches([first.model_copy(update={"home_goals": 3})])
    assert repository.matches()[0].home_goals == 3
    assert len(inspect(repository.engine).get_table_names()) == 16


def test_saved_prediction_is_immutable(repository):
    now = datetime.now(UTC)
    fixture = match().model_copy(
        update={
            "kickoff": now + timedelta(days=1),
            "status": "scheduled",
            "home_goals": None,
            "away_goals": None,
            "available_at": None,
        }
    )
    repository.sync_matches([fixture])
    repository.save_model({"version": "v1", "trained_at": now.isoformat()})
    payload = {
        "prediction_id": "p1",
        "model_version": "v1",
        "generated_at": now.isoformat(),
        "probabilities": {"home": 0.5, "draw": 0.3, "away": 0.2},
    }
    repository.save_prediction(payload, fixture)
    with pytest.raises(ValueError, match="immutable"), Session(repository.engine) as session:
        row = session.get(Prediction, "p1")
        row.payload = {"tampered": True}
        session.commit()
    assert repository.prediction("p1")["probabilities"]["home"] == 0.5
    with pytest.raises(ValueError, match="before"):
        repository.save_prediction(
            {**payload, "generated_at": fixture.kickoff.isoformat()}, fixture
        )


@pytest.mark.postgres
def test_postgres_migration_and_roundtrip():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL not configured")
    repository = Repository(Settings(database_url=url))
    repository.sync_matches([match()])
    assert any(m.id == "0" for m in repository.matches())
