"""Central configuration; paths are independent of the calling directory."""

from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FOOTBALL_AI_", env_file=".env", extra="ignore")
    root: Path = Path(__file__).resolve().parents[2]
    database_url: str = "sqlite:///data/football.db"
    profile: str = "LIGHT"

    def load(self, name: str) -> dict[str, Any]:
        with (self.root / "configs" / f"{name}.yaml").open(encoding="utf-8") as stream:
            return yaml.safe_load(stream)

    def path(self, relative: str) -> Path:
        return self.root / relative

    def prepare(self) -> None:
        for directory in ["data/raw", "data/processed", "data/external", "models", "reports", "mlruns"]:
            self.path(directory).mkdir(parents=True, exist_ok=True)

    def db_url(self) -> str:
        if self.database_url.startswith("sqlite:///"):
            filename = self.database_url.removeprefix("sqlite:///")
            if filename != ":memory:" and not Path(filename).is_absolute():
                return "sqlite:///" + self.path(filename).as_posix()
        return self.database_url
