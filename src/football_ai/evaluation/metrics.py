import numpy as np
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, log_loss

from football_ai.models.base import normalize


def calibration_bins(targets, probabilities, bins=10):
    probabilities = normalize(probabilities)
    confidence = probabilities.max(axis=1)
    correct = probabilities.argmax(axis=1) == np.asarray(targets)
    output = []
    for i in range(bins):
        mask = (confidence >= i / bins) & (
            confidence < (i + 1) / bins if i < bins - 1 else confidence <= 1
        )
        output.append(
            {
                "lower": i / bins,
                "upper": (i + 1) / bins,
                "count": int(mask.sum()),
                "mean_probability": float(confidence[mask].mean()) if mask.any() else None,
                "observed_frequency": float(correct[mask].mean()) if mask.any() else None,
            }
        )
    return output


def metrics(targets, probabilities):
    targets = np.asarray(targets, dtype=int)
    probabilities = normalize(probabilities)
    one_hot = np.eye(3)[targets]
    bins = calibration_bins(targets, probabilities)
    ece = sum(
        row["count"] * abs(row["mean_probability"] - row["observed_frequency"])
        for row in bins
        if row["count"]
    ) / len(targets)
    return {
        "n": len(targets),
        "log_loss": float(log_loss(targets, probabilities, labels=[0, 1, 2])),
        "brier": float(np.square(probabilities - one_hot).sum(axis=1).mean()),
        "accuracy": float(accuracy_score(targets, probabilities.argmax(axis=1))),
        "balanced_accuracy": float(balanced_accuracy_score(targets, probabilities.argmax(axis=1))),
        "ece": float(ece),
        "mean_top_probability": float(probabilities.max(axis=1).mean()),
        "confusion_matrix": confusion_matrix(
            targets, probabilities.argmax(axis=1), labels=[0, 1, 2]
        ).tolist(),
        "calibration_bins": bins,
    }


def goal_metrics(matches, grids):
    predicted = []
    nll = []
    for match, grid in zip(matches, grids, strict=True):
        scores = np.arange(len(grid))
        predicted.append(
            [float((grid.sum(axis=1) * scores).sum()), float((grid.sum(axis=0) * scores).sum())]
        )
        hg, ag = match.home_goals, match.away_goals
        likelihood = grid[hg, ag] if hg < len(grid) and ag < len(grid) else 1e-12
        nll.append(-np.log(max(likelihood, 1e-12)))
    actual = np.array([[m.home_goals, m.away_goals] for m in matches])
    error = np.abs(np.array(predicted) - actual)
    return {
        "home_goals_mae": float(error[:, 0].mean()),
        "away_goals_mae": float(error[:, 1].mean()),
        "score_log_loss": float(np.mean(nll)),
    }
