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
