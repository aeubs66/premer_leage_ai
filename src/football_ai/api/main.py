"""Local analytics API, with clean errors and automatically generated OpenAPI."""

import json

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from football_ai.api.schemas import PredictionResponse, PredictRequest
from football_ai.config import Settings
from football_ai.data.schemas import team_name
from football_ai.database.repository import Repository
from football_ai.inference.predictor import Predictor
from football_ai.services import evaluate_saved, recent_matches, team_form, upcoming
from football_ai.training.registry import LocalRegistry


def create_app(settings: Settings | None = None):
    settings = settings or Settings()
    repository = Repository(settings)
    repository.migrate()
    app = FastAPI(
        title="Premier League AI",
        version="0.1.0",
        description="Football research and probabilistic forecasting. Outcomes are uncertain.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.get("/health")
    def health():
        return {"status": "ok", "model_available": settings.path("models/champion.json").exists()}

    @app.get("/teams")
    def teams():
        records = repository.matches()
        return sorted({m.home_team for m in records} | {m.away_team for m in records})

    @app.get("/fixtures/upcoming")
    def fixtures(days: int = Query(default=14, ge=1, le=365)):
        return [m.model_dump(mode="json") for m in upcoming(repository, days)]

    @app.get("/matches/recent")
    def results(days: int = Query(default=30, ge=1, le=365)):
        return recent_matches(repository, days)

    @app.post("/predict", response_model=PredictionResponse)
    def predict(request: PredictRequest):
        identifier = request.fixture_id
        if not identifier:
            assert request.home_team is not None and request.away_team is not None
            records = repository.matches()
            selected = [
                m
                for m in records
                if m.home_team == team_name(request.home_team)
                and m.away_team == team_name(request.away_team)
                and m.kickoff.date() == request.match_date
            ]
            if len(selected) != 1:
                raise HTTPException(404, "No unique fixture matches these teams and date")
            identifier = selected[0].id
        try:
            return Predictor(settings, repository).predict(identifier)
        except KeyError as exc:
            raise HTTPException(404, str(exc)) from exc
        except ValueError as exc:
            message = str(exc)
            raise HTTPException(503 if "No deployed model" in message else 409, message) from exc

    @app.get("/predictions/{prediction_id}", response_model=PredictionResponse)
    def prediction(prediction_id: str):
        payload = repository.prediction(prediction_id)
        if payload is None:
            raise HTTPException(404, "Prediction not found")
        return payload

    @app.get("/models")
    def models():
        pointer = settings.path("models/champion.json")
        champion = json.loads(pointer.read_text())["version"] if pointer.exists() else None
        return {"champion": champion, "versions": repository.model_manifests()}

    @app.get("/models/performance")
    def performance():
        try:
            _, manifest = LocalRegistry(settings).load()
        except ValueError:
            return {"available": False, "message": "Train a model to see measured performance"}
        report = json.loads(
            settings.path(f"reports/{manifest['version']}/metrics.json").read_text(encoding="utf-8")
        )
        return {
            "available": True,
            "version": manifest["version"],
            "report": report,
            "prospective": evaluate_saved(settings),
        }

    @app.get("/teams/{team}/form")
    def form(team: str, limit: int = Query(default=20, ge=1, le=100)):
        try:
            return team_form(repository, team_name(team), limit)
        except KeyError as exc:
            raise HTTPException(404, str(exc)) from exc

    return app
