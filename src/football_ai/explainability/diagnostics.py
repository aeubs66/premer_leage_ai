"""Feature importance measured on an explicitly held-out chronological block."""

import numpy as np

from football_ai.evaluation.metrics import metrics


def permutation_importance(model, features, matches, seed=42, repeats=3):
    """Never call this on the sealed test to make feature decisions."""
    targets = [m.outcome for m in matches]
    baseline = metrics(targets, model.predict_proba(features, matches))["log_loss"]
    rng = np.random.default_rng(seed)
    rows = []
    for column in model.columns:
        if features[column].isna().all():
            continue
        losses = []
        for _ in range(repeats):
            shuffled = features.copy()
            shuffled[column] = rng.permutation(shuffled[column].to_numpy())
            losses.append(
                metrics(targets, model.predict_proba(shuffled, matches))["log_loss"] - baseline
            )
        rows.append(
            {
                "feature": column,
                "log_loss_increase": float(np.mean(losses)),
                "standard_deviation": float(np.std(losses)),
            }
        )
    return sorted(rows, key=lambda row: row["log_loss_increase"], reverse=True)


def tree_importance(model):
    names = model.imputer.get_feature_names_out(model.columns)
    return sorted(
        [
            {"feature": str(name), "importance": float(value)}
            for name, value in zip(names, model.model.feature_importances_, strict=True)
        ],
        key=lambda row: row["importance"],
        reverse=True,
    )
