"""Command entry point; operational commands are added with their components."""

import json
from pathlib import Path

import typer

from football_ai.config import Settings
from football_ai.logging import configure_logging

app = typer.Typer(no_args_is_help=True)


@app.callback()
def main() -> None:
    configure_logging()


@app.command()
def status() -> None:
    settings = Settings()
    typer.echo(f"Root: {settings.root}\nProfile: {settings.profile}")


def display(value):
    typer.echo(json.dumps(value, indent=2, default=str))


@app.command()
def update_data(
    csv: Path | None = None,
    season: str | None = None,
    fixtures: Path | None = None,
    api_fixtures: bool = False,
    offline: bool = False,
):
    """Download or import real matches, validate, version, and rebuild cached features."""
    from football_ai.services import update_data as update

    display(update(Settings(), csv, season, fixtures, api_fixtures, offline))


@app.command()
def import_observations(path: Path):
    """Import timestamped optional enrichment as JSON Lines."""
    from football_ai.services import import_observations as ingest

    display(ingest(Settings(), path))


@app.command()
def train(neural: bool | None = None, optimization: str | None = None, tune: bool = True):
    """Select and evaluate models chronologically; initialize a champion if absent."""
    from football_ai.training.trainer import train as fit

    display(fit(Settings(), neural=neural, optimization=optimization, tune_enabled=tune))


@app.command()
def retrain(neural: bool | None = None, optimization: str | None = None, tune: bool = True):
    """Train a candidate and apply the independent-data champion comparison gate."""
    from football_ai.training.trainer import train as fit

    display(
        fit(Settings(), neural=neural, optimization=optimization, retrain=True, tune_enabled=tune)
    )


@app.command()
def predict_upcoming(days: int = 14):
    """Save new predictions only for scheduled real fixtures before kickoff."""
    from football_ai.database.repository import Repository
    from football_ai.inference.predictor import Predictor
    from football_ai.services import upcoming

    settings = Settings()
    repository = Repository(settings)
    repository.migrate()
    predictor = Predictor(settings, repository)
    results = []
    for fixture in upcoming(repository, days):
        try:
            results.append(predictor.predict(fixture.id))
        except ValueError as exc:
            results.append({"fixture_id": fixture.id, "error": str(exc)})
    display(
        results
        if results
        else {
            "message": "No upcoming fixtures. Import a fixture CSV or update-data --api-fixtures."
        }
    )


@app.command()
def record_results():
    """Attach actual results without altering saved forecasts."""
    from football_ai.database.repository import Repository

    repository = Repository(Settings())
    repository.migrate()
    display({"attached": repository.record_results()})


@app.command()
def evaluate_predictions():
    from football_ai.services import evaluate_saved

    display(evaluate_saved(Settings()))


@app.command()
def evaluate(version: str | None = None):
    """Display the sealed evaluation of an existing model, without selecting models."""
    from football_ai.training.registry import LocalRegistry

    settings = Settings()
    _, manifest = LocalRegistry(settings).load(version, research=True)
    display(json.loads(settings.path(f"reports/{manifest['version']}/metrics.json").read_text()))


@app.command()
def backtest(version: str | None = None):
    from football_ai.services import backtest as run

    display(run(Settings(), version))


@app.command()
def rollback():
    from football_ai.training.registry import LocalRegistry

    display({"champion": LocalRegistry(Settings()).rollback()})


@app.command()
def api(host: str = "127.0.0.1", port: int = 8000):
    """Start the local FastAPI server and its OpenAPI documentation."""
    import uvicorn

    uvicorn.run("football_ai.api.main:create_app", factory=True, host=host, port=port)
