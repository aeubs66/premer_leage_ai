"""Command entry point; operational commands are added with their components."""

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
