"""Small, serial Optuna searches scored using inner chronological folds."""

import numpy as np
from sklearn.metrics import log_loss

from football_ai.models.boosting import BoostingModel
from football_ai.models.neural import NeuralModel
from football_ai.training.splits import walk_folds


def tune(features, matches, defaults, training, profile, kind="xgboost"):
    import optuna

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    budget = training["tuning"][training["optimization"]]
    inner = list(walk_folds(matches, warmup=max(100, len(matches) // 2), blocks=2))

    def objective(trial):
        if kind == "xgboost":
            parameters = {
                **defaults,
                "max_depth": trial.suggest_int("max_depth", 2, 4),
                "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.12, log=True),
                "n_estimators": trial.suggest_int("n_estimators", 80, 250, step=10),
                "min_child_weight": trial.suggest_int("min_child_weight", 3, 12),
                "subsample": trial.suggest_float("subsample", 0.7, 1),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1),
                "reg_lambda": trial.suggest_float("reg_lambda", 1, 20, log=True),
            }
        else:
            parameters = {
                **defaults,
                "embedding_size": trial.suggest_int("embedding_size", 2, 6),
                "dropout": trial.suggest_float("dropout", 0.1, 0.4),
                "learning_rate": trial.suggest_float("learning_rate", 0.0003, 0.003, log=True),
                "weight_decay": trial.suggest_float("weight_decay", 0.001, 0.05, log=True),
            }
        losses = []
        for train, validation in inner:
            model = (
                BoostingModel(parameters, profile["threads"], training["seed"])
                if kind == "xgboost"
                else NeuralModel(
                    parameters,
                    profile["neural_width"],
                    profile["neural_epochs"],
                    profile["threads"],
                    training["seed"],
                )
            )
            model.fit(features.iloc[train], [matches[i] for i in train])
            probabilities = model.predict_proba(
                features.iloc[validation], [matches[i] for i in validation]
            )
            losses.append(
                log_loss([matches[i].outcome for i in validation], probabilities, labels=[0, 1, 2])
            )
        return float(np.mean(losses))

    study = optuna.create_study(
        direction="minimize", sampler=optuna.samplers.TPESampler(seed=training["seed"])
    )
    study.optimize(
        objective, n_trials=budget["trials"], timeout=budget["timeout_seconds"], n_jobs=1
    )
    return {**defaults, **study.best_params}, [
        {"number": t.number, "value": t.value, "parameters": t.params, "state": t.state.name}
        for t in study.trials
    ]
