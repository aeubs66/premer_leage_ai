"""MLflow stays local; a SQLite tracking database avoids a cloud dependency."""

import logging
from pathlib import Path

from football_ai.config import Settings

log = logging.getLogger(__name__)


def track(settings: Settings, manifest: dict, report: dict, directory: Path):
    if not manifest["training_config"].get("tracking", True):
        return None
    import mlflow

    mlflow.set_tracking_uri("sqlite:///" + settings.path("mlruns/tracking.db").as_posix())
    mlflow.set_experiment("premier-league-chronological")
    with mlflow.start_run(run_name=manifest["version"]) as run:
        for key in [
            "git_commit",
            "dataset_version",
            "feature_version",
            "trained_at",
            "python_version",
            "seed",
        ]:
            mlflow.set_tag(key, manifest[key])
        mlflow.log_params(
            {
                "profile": manifest["profile"],
                "ensemble": manifest["ensemble"],
                "calibration": manifest["calibration"],
                "optimization": manifest["training_config"]["optimization"],
            }
        )
        for split in ["validation", "test"]:
            mlflow.log_metrics(
                {
                    f"{split}_{key}": report[split][key]
                    for key in ["log_loss", "brier", "accuracy", "ece"]
                }
            )
        mlflow.log_dict(manifest, "configuration.json")
        mlflow.log_artifacts(str(directory), "reports")
        mlflow.log_artifacts(str(settings.path(f"models/{manifest['version']}")), "model")
        return run.info.run_id
