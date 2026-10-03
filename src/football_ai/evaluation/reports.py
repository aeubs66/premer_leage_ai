"""JSON, HTML, CSV, and portable figures generated from measured predictions."""

import html
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def write_report(directory: Path, report: dict, predictions: pd.DataFrame | None = None):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if predictions is not None:
        predictions.to_csv(directory / "predictions.csv", index=False)
    comparison = report.get("comparison", {})
    if comparison:
        names = list(comparison)
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        for ax, metric in zip(axes, ["log_loss", "brier"], strict=True):
            ax.barh(names, [comparison[n][metric] for n in names])
            ax.set_title(f"Selection {metric} (lower is better)")
        fig.tight_layout()
        fig.savefig(directory / "model-comparison.png", dpi=150)
        plt.close(fig)
    for split in ["validation", "test"]:
        if split not in report:
            continue
        bins = report[split]["calibration_bins"]
        fig, ax = plt.subplots(figsize=(6, 5))
        ax.plot([0, 1], [0, 1], "--", color="gray")
        populated = [row for row in bins if row["count"]]
        ax.plot(
            [row["mean_probability"] for row in populated],
            [row["observed_frequency"] for row in populated],
            "o-",
        )
        ax.set(
            xlabel="Predicted top-outcome probability",
            ylabel="Observed correctness",
            title=f"{split.capitalize()} reliability",
        )
        fig.tight_layout()
        fig.savefig(directory / f"{split}-calibration.png", dpi=150)
        plt.close(fig)
    if predictions is not None and not predictions.empty and "actual" in predictions:
        chosen = predictions[["home", "draw", "away"]].to_numpy().argmax(axis=1)
        fig, ax = plt.subplots(figsize=(9, 4))
        pd.Series(chosen == predictions.actual.to_numpy()).rolling(50, min_periods=20).mean().plot(
            ax=ax
        )
        ax.set(
            title="Historical correctness over 50 predictions",
            xlabel="Chronological prediction",
            ylabel="Fraction correct",
        )
        fig.tight_layout()
        fig.savefig(directory / "historical-performance.png", dpi=150)
        plt.close(fig)
    body = html.escape(json.dumps(report, indent=2))
    images = "".join(
        f'<figure><img width="800" src="{p.name}"/><figcaption>{p.stem}</figcaption></figure>'
        for p in directory.glob("*.png")
    )
    (directory / "report.html").write_text(
        f'<!doctype html><meta charset="utf-8"><title>Football AI evaluation</title><style>body{{font:16px system-ui;max-width:1100px;margin:40px auto;background:#f7f9fc;color:#15243a}}pre{{white-space:pre-wrap}}img{{max-width:100%}}</style><h1>Football AI evaluation</h1><p>Historical research; these results do not guarantee future outcomes.</p>{images}<pre>{body}</pre>',
        encoding="utf-8",
    )


def disagreement(predictions: dict) -> np.ndarray:
    from scipy.special import entr

    tensor = np.stack(list(predictions.values()), axis=1)
    mean = tensor.mean(axis=1)
    # Jensen–Shannon divergence, bounded and independent of the predicted winner.
    return entr(mean).sum(axis=1) - entr(tensor).sum(axis=2).mean(axis=1)
