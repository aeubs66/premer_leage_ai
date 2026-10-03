"""Actual fitted models on explicit synthetic test records; no performance claims."""

import shutil
from datetime import UTC, datetime, timedelta

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from test_data import match

from football_ai.api.main import create_app
from football_ai.config import Settings
from football_ai.database import repository as repo_module
from football_ai.database.models import Prediction
from football_ai.database.repository import Repository
from football_ai.features.pipeline import FeaturePipeline
from football_ai.models.calibration import Calibrator
from football_ai.models.ensemble import Ensemble
from football_ai.services import evaluate_saved
from football_ai.training.registry import LocalRegistry
from football_ai.training.trainer import Artifact, create_models, fit_models


def test_predict_save_result_and_evaluate(tmp_path, monkeypatch):
    base = Settings().root
    shutil.copytree(base / "configs", tmp_path / "configs")
    shutil.copytree(
        base / "src/football_ai/database/migrations",
        tmp_path / "src/football_ai/database/migrations",
    )
    shutil.copy(base / "alembic.ini", tmp_path / "alembic.ini")
    settings = Settings(root=tmp_path)
    repository = Repository(settings)
    records = [match(i, hg=i % 3, ag=1) for i in range(60)]
    now = datetime.now(UTC)
    fixture = match(100).model_copy(
        update={
            "kickoff": now + timedelta(days=1),
            "status": "scheduled",
            "home_goals": None,
            "away_goals": None,
            "available_at": None,
        }
    )
    repository.sync_matches(records + [fixture])
    feature_config = settings.load("features")
    features = FeaturePipeline(feature_config).transform(records)
    training = settings.load("training")
    training["neural"] = False
    model_config = settings.load("models")
    model_config["xgboost"]["n_estimators"] = 10
    profile = training["profiles"]["LIGHT"]
    models = fit_models(create_models(model_config, training, profile), features, records)
    ensemble = Ensemble("single", ["elo"])
    diagnostics = {
        "disagreement_quantiles": [0.01, 0.03],
        "probability_quantiles": [0.4, 0.6],
        "validation_n": 100,
        "validation_ece": 0.05,
        "calibration_bins": [
            {
                "lower": 0,
                "upper": 1,
                "count": 100,
                "mean_probability": 0.5,
                "observed_frequency": 0.5,
            }
        ],
    }
    recipe = {
        "score_model": "poisson",
        "feature_config": feature_config,
        "models_config": model_config,
        "training_config": training,
        "profile_config": profile,
        "boost_parameters": model_config["xgboost"],
    }
    artifact = Artifact(models, ensemble, Calibrator(), recipe, diagnostics)
    manifest = {
        "version": "abc123",
        "trained_at": now.isoformat(),
        "data_cutoff": max(m.result_available_at for m in records).isoformat(),
        "dataset_version": "synthetic-test-only",
        "feature_version": "test",
    }
    registry = LocalRegistry(settings)
    registry.save("abc123", artifact, artifact, manifest)
    registry.promote("abc123")
    repository.save_model(manifest)
    client = TestClient(create_app(settings))
    response = client.post("/predict", json={"fixture_id": fixture.id})
    assert response.status_code == 200, response.text
    payload = response.json()
    assert sum(payload["probabilities"].values()) == pytest.approx(1)
    assert sum(map(sum, payload["score_matrix"])) + payload[
        "other_scores_probability"
    ] == pytest.approx(1)
    assert datetime.fromisoformat(payload["generated_at"].replace("Z", "+00:00")) < fixture.kickoff
    assert payload["explanation"]["factors"]
    identifier = payload["prediction_id"]
    stored = repository.prediction(identifier)
    with pytest.raises(IntegrityError), repository.engine.begin() as connection:
        connection.execute(
            update(Prediction).where(Prediction.id == identifier).values(payload={"tampered": True})
        )
    result = fixture.model_copy(
        update={
            "status": "finished",
            "home_goals": 2,
            "away_goals": 1,
            "available_at": fixture.kickoff + timedelta(hours=3),
        }
    )
    repository.sync_matches([result])

    class Later(datetime):
        @classmethod
        def now(cls, tz=None):
            return now + timedelta(days=2)

    monkeypatch.setattr(repo_module, "datetime", Later)
    assert repository.record_results() == 1
    attached = repository.prediction(identifier)
    assert attached["probabilities"] == stored["probabilities"]
    assert attached["result"]["home_goals"] == 2
    assert evaluate_saved(settings)["abc123"]["n"] == 1
    assert client.post("/predict", json={"fixture_id": fixture.id}).status_code == 409


def test_optional_observations_obey_publication_cutoff():
    from football_ai.data.schemas import Observation

    fixture = match(1)
    publication = fixture.kickoff - timedelta(hours=1)
    observation = Observation(
        team="A",
        fixture_id=fixture.id,
        kind="availability",
        observed_at=publication,
        available_at=publication,
        values={"unavailable_players": 2, "missing_minutes": 180},
        source="test",
    )
    config = Settings().load("features")
    pipeline = FeaturePipeline(config, [observation])
    assert np.isnan(pipeline.for_fixture([], fixture, publication).home_unavailable_players.iloc[0])
    assert pipeline.for_fixture([], fixture).home_unavailable_players.iloc[0] == 2
