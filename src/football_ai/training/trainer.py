"""Nested time-aware model selection followed by a sealed seasonal evaluation."""

import importlib.metadata
import json
import logging
import platform
import subprocess
import uuid
from datetime import UTC, datetime

import numpy as np
import pandas as pd

from football_ai.config import Settings
from football_ai.data.store import load_snapshot
from football_ai.database.repository import Repository
from football_ai.evaluation.metrics import calibration_bins, goal_metrics, metrics
from football_ai.evaluation.reports import disagreement, write_report
from football_ai.features.pipeline import FeaturePipeline
from football_ai.models.baseline import Baseline
from football_ai.models.boosting import BoostingModel
from football_ai.models.calibration import Calibrator
from football_ai.models.elo import EloModel
from football_ai.models.ensemble import Ensemble
from football_ai.models.neural import NeuralModel
from football_ai.models.poisson import PoissonModel, reconcile_scores
from football_ai.training.registry import LocalRegistry
from football_ai.training.splits import meta_partitions, season_split, walk_folds
from football_ai.training.tracking import track
from football_ai.training.tuning import tune

log = logging.getLogger(__name__)


def create_models(config, training, profile, boost_parameters=None):
    models = {
        "home_baseline": Baseline("home"),
        "frequency": Baseline(),
        "previous_season": Baseline("previous_season"),
        "elo": EloModel(),
        "poisson": PoissonModel(**config["poisson"]),
        "dixon_coles": PoissonModel(**{**config["poisson"], "dixon_coles": True}),
        "xgboost": BoostingModel(
            boost_parameters or config["xgboost"], profile["threads"], training["seed"]
        ),
        "xgboost_no_h2h": BoostingModel(
            boost_parameters or config["xgboost"],
            profile["threads"],
            training["seed"],
            exclude_head_to_head=True,
        ),
    }
    if training.get("neural"):
        models["neural"] = NeuralModel(
            config["neural"],
            profile["neural_width"],
            profile["neural_epochs"],
            profile["threads"],
            training["seed"],
        )
    return models


def fit_models(models, features, matches):
    if set(m.outcome for m in matches) != {0, 1, 2}:
        raise ValueError("Training requires all three outcomes")
    for name, model in models.items():
        log.info("Fitting %s on %d matches", name, len(matches))
        model.fit(features, matches)
    return models


class Artifact:
    def __init__(self, models, ensemble, calibrator, recipe, diagnostics):
        self.models, self.ensemble, self.calibrator = models, ensemble, calibrator
        self.recipe, self.diagnostics = recipe, diagnostics

    def predict(self, features, matches):
        individual = {
            name: model.predict_proba(features, matches) for name, model in self.models.items()
        }
        probabilities = self.calibrator.transform(self.ensemble.predict_proba(individual))
        score_model = self.models[self.recipe["score_model"]]
        grids = [
            reconcile_scores(grid, p)
            for grid, p in zip(score_model.grids(matches), probabilities, strict=True)
        ]
        return probabilities, grids, individual

    def refit(self, features, matches):
        import copy

        cloned = copy.deepcopy(self)
        cloned.models = fit_models(
            create_models(
                cloned.recipe["models_config"],
                cloned.recipe["training_config"],
                cloned.recipe["profile_config"],
                cloned.recipe["boost_parameters"],
            ),
            features,
            matches,
        )
        return cloned


def feature_frame(settings, records, version, observations):
    import hashlib

    config = settings.load("features")
    identity = hashlib.sha256(
        json.dumps(
            {"features": config, "observations": [o.model_dump(mode="json") for o in observations]},
            sort_keys=True,
        ).encode()
    ).hexdigest()[:16]
    cache = settings.path(f"data/processed/features-{version}-{identity}.csv")
    if cache.exists():
        return pd.read_csv(cache, index_col="match_id"), f"{config['version']}-{identity}"
    frame = FeaturePipeline(config, observations).transform(records)
    frame.to_csv(cache)
    return frame, f"{config['version']}-{identity}"


def train(settings: Settings, neural=None, optimization=None, retrain=False, tune_enabled=True):
    settings.prepare()
    repository = Repository(settings)
    repository.migrate()
    records, dataset_version = load_snapshot(settings)
    now = datetime.now(UTC)
    matches = [m for m in records if m.status == "finished" and m.result_available_at < now]
    observations = repository.observations()
    frame, feature_version = feature_frame(settings, records, dataset_version, observations)
    features = frame.loc[[m.id for m in matches]]
    training = settings.load("training")
    if neural is not None:
        training["neural"] = neural
    if optimization:
        training["optimization"] = optimization.upper()
    profile = training["profiles"][settings.profile.upper()]
    config = settings.load("models")
    pretest, test_indices, prospective_indices, test_season = season_split(matches)
    development = [matches[i] for i in pretest]
    dev_features = features.iloc[pretest]
    all_predictions: dict[str, list] = {}
    oof_matches, oof_indices, lineage, trials = [], [], [], []
    boost_parameters = config["xgboost"]
    diagnostic_model = None
    diagnostic_indices = []
    for fold, (train_indices, validation_indices) in enumerate(
        walk_folds(development, training["warmup_matches"], training["validation_blocks"])
    ):
        train_matches = [development[i] for i in train_indices]
        validation_matches = [development[i] for i in validation_indices]
        log.info(
            "Outer fold %d: train=%d validation=%d",
            fold + 1,
            len(train_indices),
            len(validation_indices),
        )
        if tune_enabled:
            boost_parameters, trial_records = tune(
                dev_features.iloc[train_indices],
                train_matches,
                config["xgboost"],
                training,
                profile,
            )
            trials.append({"fold": fold, "trials": trial_records})
        if training.get("tune_neural") and training.get("neural"):
            config["neural"], neural_trials = tune(
                dev_features.iloc[train_indices],
                train_matches,
                config["neural"],
                training,
                profile,
                "neural",
            )
            trials.append({"fold": fold, "neural_trials": neural_trials})
        models = fit_models(
            create_models(config, training, profile, boost_parameters),
            dev_features.iloc[train_indices],
            train_matches,
        )
        diagnostic_model = models["xgboost"]
        diagnostic_indices = validation_indices
        for name, model in models.items():
            all_predictions.setdefault(name, []).append(
                model.predict_proba(dev_features.iloc[validation_indices], validation_matches)
            )
        oof_matches.extend(validation_matches)
        oof_indices.extend(validation_indices)
        lineage.append(
            {
                "fold": fold,
                "training_last_available_at": max(
                    m.result_available_at for m in train_matches
                ).isoformat(),
                "prediction_cutoff": min(m.kickoff for m in validation_matches).isoformat(),
                "train_ids": [m.id for m in train_matches],
                "prediction_ids": [m.id for m in validation_matches],
            }
        )
    predictions = {name: np.concatenate(rows) for name, rows in all_predictions.items()}
    targets = np.array([m.outcome for m in oof_matches])
    fit_indices, calibration_indices, selection_indices = meta_partitions(oof_matches)

    def part(indices):
        return {name: p[indices] for name, p in predictions.items()}

    score_model = min(
        ["poisson", "dixon_coles"],
        key=lambda n: metrics(targets[selection_indices], predictions[n][selection_indices])[
            "log_loss"
        ],
    )
    comparison = {
        name: metrics(targets[selection_indices], p[selection_indices])
        for name, p in predictions.items()
    }
    candidates = []
    core = ["elo", score_model, "xgboost"]
    if comparison["xgboost_no_h2h"]["log_loss"] < comparison["xgboost"]["log_loss"]:
        core[-1] = "xgboost_no_h2h"
    name_sets = [core] + ([core + ["neural"]] if "neural" in predictions else [])
    ensembles = [Ensemble("single", [name]) for name in predictions]
    ensembles += [
        Ensemble(kind, names, training["seed"])
        for names in name_sets
        for kind in ["weighted", "logistic", "meta"]
    ]
    for ensemble in ensembles:
        ensemble.fit(part(fit_indices), targets[fit_indices])
        for kind in ["none", "temperature", "sigmoid", "isotonic"]:
            calibrator = Calibrator(kind).fit(
                ensemble.predict_proba(part(calibration_indices)), targets[calibration_indices]
            )
            p = calibrator.transform(ensemble.predict_proba(part(selection_indices)))
            measured = metrics(targets[selection_indices], p)
            candidates.append(
                (measured["log_loss"], measured["brier"], ensemble, calibrator, p, measured)
            )
    _, _, ensemble, calibrator, selected_probabilities, validation_metrics = min(
        candidates, key=lambda item: (item[0], item[1])
    )
    comparison["selected"] = validation_metrics
    selected_base = {name: predictions[name][selection_indices] for name in ensemble.names}
    js = disagreement(selected_base)
    diagnostics = {
        "disagreement_quantiles": np.quantile(js, [1 / 3, 2 / 3]).tolist(),
        "probability_quantiles": np.quantile(
            selected_probabilities.max(axis=1), [1 / 3, 2 / 3]
        ).tolist(),
        "calibration_bins": calibration_bins(targets[selection_indices], selected_probabilities),
        "validation_n": len(selection_indices),
        "validation_ece": validation_metrics["ece"],
    }
    recipe = {
        "models_config": config,
        "training_config": training,
        "profile_config": profile,
        "boost_parameters": boost_parameters,
        "feature_config": settings.load("features"),
        "score_model": score_model,
    }
    models = fit_models(
        create_models(config, training, profile, boost_parameters), dev_features, development
    )
    research = Artifact(models, ensemble, calibrator, recipe, diagnostics)
    test_matches = [matches[i] for i in test_indices]
    test_probabilities, grids, individual_test = research.predict(
        features.iloc[test_indices], test_matches
    )
    version = uuid.uuid4().hex[:16]
    directory = settings.path(f"reports/{version}")
    report = {
        "version": version,
        "test_season": test_season,
        "test_policy": "sealed; never used for model selection",
        "ensemble": {"kind": ensemble.kind, "members": ensemble.names},
        "calibration": calibrator.kind,
        "comparison": comparison,
        "validation": validation_metrics,
        "test": {
            **metrics([m.outcome for m in test_matches], test_probabilities),
            **goal_metrics(test_matches, grids),
        },
        "individual_test": {
            name: metrics([m.outcome for m in test_matches], p)
            for name, p in individual_test.items()
        },
        "selection_candidates": [
            {
                "ensemble": e.kind,
                "members": e.names,
                "calibration": c.kind,
                "log_loss": loss,
                "brier": brier,
            }
            for loss, brier, e, c, _, _ in candidates
        ],
        "lineage": lineage,
        "tuning": trials,
        "limitations": [
            "Historical CSV result availability is assumed, not a verified publication archive.",
            "Missing enrichment is excluded; no guarantee of superiority to simple baselines.",
            "Confidence diagnostics use finite historical samples and may drift.",
        ],
    }
    rows = pd.DataFrame(
        [
            {
                "match_id": m.id,
                "kickoff": m.kickoff.isoformat(),
                "home_team": m.home_team,
                "away_team": m.away_team,
                "home": float(p[0]),
                "draw": float(p[1]),
                "away": float(p[2]),
                "actual": m.outcome,
                "kind": "retrospective_sealed_test",
                "model_version": version,
            }
            for m, p in zip(test_matches, test_probabilities, strict=True)
        ]
    )
    write_report(directory, report, rows)
    if diagnostic_model is not None:
        import matplotlib.pyplot as plt

        from football_ai.explainability.diagnostics import permutation_importance, tree_importance

        diagnostic_matches = [development[i] for i in diagnostic_indices]
        importance = permutation_importance(
            diagnostic_model,
            dev_features.iloc[diagnostic_indices],
            diagnostic_matches,
            training["seed"],
        )
        pd.DataFrame(importance).to_csv(directory / "permutation-importance.csv", index=False)
        (directory / "tree-importance.json").write_text(
            json.dumps(tree_importance(models["xgboost"]), indent=2), encoding="utf-8"
        )
        top = importance[:15][::-1]
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.barh([row["feature"] for row in top], [row["log_loss_increase"] for row in top])
        ax.set_title("Permutation importance on the last independent development fold")
        ax.set_xlabel("Increase in log loss after permutation")
        fig.tight_layout()
        fig.savefig(directory / "feature-importance.png", dpi=150)
        plt.close(fig)
    pd.DataFrame(
        [
            {
                "match_id": m.id,
                "kickoff": m.kickoff.isoformat(),
                "actual": m.outcome,
                **{
                    f"{name}_{label}": float(predictions[name][i, j])
                    for name in predictions
                    for j, label in enumerate(["home", "draw", "away"])
                },
            }
            for i, m in enumerate(oof_matches)
        ]
    ).to_csv(directory / "oof-predictions.csv", index=False)
    # Production can learn from the sealed season only after all selection is frozen.
    production = research.refit(features, matches)
    git_commit = (
        subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=settings.root, capture_output=True, text=True
        ).stdout.strip()
        or "uncommitted"
    )
    manifest = {
        "version": version,
        "trained_at": datetime.now(UTC).isoformat(),
        "data_cutoff": max(m.result_available_at for m in matches).isoformat(),
        "research_cutoff": max(m.result_available_at for m in development).isoformat(),
        "dataset_version": dataset_version,
        "feature_version": feature_version,
        "python_version": platform.python_version(),
        "git_commit": git_commit,
        "seed": training["seed"],
        "profile": settings.profile,
        "training_config": training,
        "models_config": config,
        "boost_parameters": boost_parameters,
        "dependencies": {
            package: importlib.metadata.version(package)
            for package in ["numpy", "pandas", "scipy", "scikit-learn", "xgboost", "pydantic"]
        },
        "ensemble": ensemble.kind,
        "members": ensemble.names,
        "calibration": calibrator.kind,
        "test_season": test_season,
        "validation": validation_metrics,
        "test": report["test"],
        "promotion": "candidate",
    }
    import hashlib
    import zipfile

    code_paths = sorted(settings.path("src/football_ai").rglob("*.py"))
    source_digest = hashlib.sha256()
    with zipfile.ZipFile(
        directory / "source.zip", "w", compression=zipfile.ZIP_DEFLATED
    ) as archive:
        for path in code_paths:
            source_digest.update(path.relative_to(settings.root).as_posix().encode())
            source_digest.update(path.read_bytes())
            archive.write(path, path.relative_to(settings.root))
        for path in [settings.path("pyproject.toml"), settings.path("uv.lock")]:
            archive.write(path, path.name)
    manifest["source_sha256"] = source_digest.hexdigest()
    manifest["git_dirty"] = bool(
        subprocess.run(
            ["git", "status", "--porcelain"], cwd=settings.root, capture_output=True, text=True
        ).stdout.strip()
    )
    registry = LocalRegistry(settings)
    if retrain and settings.path("models/champion.json").exists():
        champion, champion_manifest = registry.load()
        if champion_manifest["dataset_version"] == dataset_version:
            manifest["promotion"] = "rejected_no_new_dataset"
        else:
            previous_records, _ = load_snapshot(settings, champion_manifest["dataset_version"])
            old_ids = {m.id for m in previous_records if m.status == "finished"}
            new_matches = [
                m
                for m in matches
                if m.id not in old_ids
                and m.result_available_at > datetime.fromisoformat(champion_manifest["data_cutoff"])
            ]
            if len(new_matches) < 40:
                manifest["promotion"] = "pending_at_least_40_new_matches"
            else:
                cutoff = min(m.kickoff for m in new_matches)
                prefix = [m for m in matches if m.result_available_at < cutoff]
                if champion.recipe["feature_config"] != research.recipe["feature_config"]:
                    manifest["promotion"] = "pending_feature_version_review"
                else:
                    xprefix = features.loc[[m.id for m in prefix]]
                    xnew = features.loc[[m.id for m in new_matches]]
                    old_replayed = champion.refit(xprefix, prefix)
                    # Candidate recipe selection must itself predate the fresh comparison window.
                    if max(development[i].kickoff for i in oof_indices) >= cutoff:
                        manifest["promotion"] = "pending_independent_future_window"
                    else:
                        new_replayed = research.refit(xprefix, prefix)
                        old_metrics = metrics(
                            [m.outcome for m in new_matches],
                            old_replayed.predict(xnew, new_matches)[0],
                        )
                        new_metrics = metrics(
                            [m.outcome for m in new_matches],
                            new_replayed.predict(xnew, new_matches)[0],
                        )
                        manifest["promotion_comparison"] = {
                            "champion": old_metrics,
                            "candidate": new_metrics,
                        }
                        if (
                            new_metrics["log_loss"] < old_metrics["log_loss"]
                            and new_metrics["brier"] <= old_metrics["brier"]
                        ):
                            manifest["promotion"] = "promoted"
                        else:
                            manifest["promotion"] = "rejected_validation"
    elif not settings.path("models/champion.json").exists():
        manifest["promotion"] = "initial_champion"
    else:
        manifest["promotion"] = "candidate_requires_retrain_gate"
    registry.save(version, research, production, manifest)
    run_id = track(settings, manifest, report, directory)
    manifest["mlflow_run_id"] = run_id
    settings.path(f"models/{version}/manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    repository.save_model(manifest)
    if manifest["promotion"] in ("initial_champion", "promoted"):
        registry.promote(version)
    log.info(
        "Saved version %s: %s; validation log loss %.4f; test log loss %.4f",
        version,
        manifest["promotion"],
        validation_metrics["log_loss"],
        report["test"]["log_loss"],
    )
    return manifest
