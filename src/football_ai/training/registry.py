"""Content-audited local artifact registry with atomic champion pointers."""

import hashlib
import json
from typing import Protocol

import joblib
import numpy as np

from football_ai.config import Settings


def promotion_allowed(champion: dict, candidate: dict) -> bool:
    values = [champion["log_loss"], champion["brier"], candidate["log_loss"], candidate["brier"]]
    if not np.isfinite(values).all():
        return False
    return bool(
        candidate["log_loss"] < champion["log_loss"] and candidate["brier"] <= champion["brier"]
    )


class ModelRegistry(Protocol):
    def load(self, version: str | None = None, research: bool = False): ...
    def promote(self, version: str): ...


class LocalRegistry:
    def __init__(self, settings: Settings):
        self.settings = settings
        settings.prepare()

    def save(self, version, research, production, manifest):
        directory = self.settings.path(f"models/{version}")
        directory.mkdir(parents=True, exist_ok=False)
        for name, artifact in [("research", research), ("production", production)]:
            path = directory / f"{name}.joblib"
            joblib.dump(artifact, path)
            manifest[f"{name}_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        (directory / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        self.settings.path("models/latest.json").write_text(
            json.dumps({"version": version}), encoding="utf-8"
        )

    def load(self, version=None, research=False):
        if version is None:
            path = self.settings.path("models/champion.json")
            if not path.exists():
                raise ValueError("No deployed model. Run football-ai train.")
            version = json.loads(path.read_text())["version"]
        if not version.isalnum():
            raise ValueError("Invalid model version")
        directory = self.settings.path(f"models/{version}")
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        name = "research" if research else "production"
        path = directory / f"{name}.joblib"
        if hashlib.sha256(path.read_bytes()).hexdigest() != manifest[f"{name}_sha256"]:
            raise ValueError("Artifact checksum mismatch")
        # Only trusted local artifacts are loaded; API never accepts artifact uploads.
        return joblib.load(path), manifest

    def promote(self, version):
        self.load(version)
        pointer = self.settings.path("models/champion.json")
        previous = json.loads(pointer.read_text())["version"] if pointer.exists() else None
        temporary = pointer.with_suffix(".tmp")
        temporary.write_text(
            json.dumps({"version": version, "previous": previous}, indent=2), encoding="utf-8"
        )
        temporary.replace(pointer)

    def rollback(self):
        pointer = self.settings.path("models/champion.json")
        previous = json.loads(pointer.read_text()).get("previous")
        if not previous:
            raise ValueError("No previous champion")
        self.promote(previous)
        return previous
