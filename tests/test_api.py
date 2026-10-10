from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from test_data import match

from football_ai.api.main import create_app
from football_ai.config import Settings
from football_ai.database.repository import Repository


def test_api_validation_unknown_teams_and_no_model(tmp_path):
    settings = Settings(
        root=Settings().root, database_url="sqlite:///" + (tmp_path / "api.db").as_posix()
    )
    repository = Repository(settings)
    fixture = match().model_copy(
        update={
            "kickoff": datetime.now(UTC) + timedelta(days=2),
            "status": "scheduled",
            "home_goals": None,
            "away_goals": None,
            "available_at": None,
        }
    )
    repository.sync_matches([match(1), fixture])
    client = TestClient(create_app(settings))
    assert client.get("/health").status_code == 200
    assert client.get("/teams").json() == ["A", "B"]
    assert len(client.get("/fixtures/upcoming").json()) == 1
    assert client.post("/predict", json={}).status_code == 422
    assert (
        client.post(
            "/predict", json={"home_team": "A", "away_team": "A", "match_date": "2030-01-01"}
        ).status_code
        == 422
    )
    assert client.post("/predict", json={"fixture_id": "missing"}).status_code == 404
    assert client.get("/teams/missing/form").status_code == 404
    assert client.get("/predictions/missing").status_code == 404
    assert "/predict" in client.get("/openapi.json").json()["paths"]


def test_recent_matches_keeps_started_fixtures_and_hides_unavailable_scores(tmp_path):
    settings = Settings(
        root=Settings().root, database_url="sqlite:///" + (tmp_path / "results.db").as_posix()
    )
    repo = Repository(settings)
    now = datetime.now(UTC)
    finished = match(1, hg=0, ag=0).model_copy(
        update={"kickoff": now - timedelta(hours=4), "available_at": now - timedelta(hours=1)}
    )
    waiting = match(2).model_copy(
        update={
            "kickoff": now - timedelta(hours=1),
            "status": "scheduled",
            "home_goals": None,
            "away_goals": None,
            "available_at": None,
        }
    )
    unavailable = match(3).model_copy(
        update={"kickoff": now - timedelta(hours=2), "available_at": now + timedelta(hours=1)}
    )
    future = waiting.model_copy(update={"id": "future", "kickoff": now + timedelta(hours=2)})
    repo.sync_matches([finished, waiting, unavailable, future, match(4)])
    client = TestClient(create_app(settings))
    rows = client.get("/matches/recent?days=1").json()
    assert len(rows) == 3
    assert rows[0]["id"] == waiting.id
    assert rows[0]["display_status"] == "awaiting_result"
    assert rows[0]["home_goals"] is None
    assert rows[1]["home_goals"] is None
    assert rows[2]["display_status"] == "finished"
    assert rows[2]["home_goals"] == rows[2]["away_goals"] == 0
    assert client.get("/matches/recent?days=0").status_code == 422
