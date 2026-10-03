import numpy as np
from test_data import match

from football_ai.evaluation.metrics import metrics
from football_ai.models.calibration import Calibrator
from football_ai.models.ensemble import Ensemble
from football_ai.training.registry import promotion_allowed
from football_ai.training.splits import meta_partitions, walk_folds


def test_walk_folds_respect_result_availability():
    records = [match(i, hg=i % 3, ag=(i + 1) % 3) for i in range(100)]
    for train, validation in walk_folds(records, warmup=30, blocks=4):
        cutoff = min(records[i].kickoff for i in validation)
        assert all(records[i].available_at < cutoff for i in train)
        assert set(train).isdisjoint(validation)
    fit, cal, selection = meta_partitions(records * 0 + [match(i) for i in range(200)])
    assert max(fit) < min(cal) < max(cal) < min(selection)


def test_calibration_and_ensemble_only_use_passed_blocks():
    rng = np.random.default_rng(42)
    probabilities = rng.dirichlet([3, 2, 2], 180)
    labels = np.arange(180) % 3
    predictions = {"a": probabilities, "b": probabilities[:, [2, 1, 0]]}
    for kind in ["weighted", "logistic", "meta"]:
        ensemble = Ensemble(kind, ["a", "b"]).fit(
            {k: v[:90] for k, v in predictions.items()}, labels[:90]
        )
        result = ensemble.predict_proba({k: v[135:] for k, v in predictions.items()})
        np.testing.assert_allclose(result.sum(axis=1), 1)
    for kind in ["none", "temperature", "sigmoid", "isotonic"]:
        calibrator = Calibrator(kind).fit(probabilities[90:135], labels[90:135])
        np.testing.assert_allclose(calibrator.transform(probabilities[135:]).sum(axis=1), 1)
    assert metrics(labels, probabilities)["n"] == 180


def test_deployment_requires_both_probability_metrics():
    champion = {"log_loss": 1.0, "brier": 0.6}
    assert promotion_allowed(champion, {"log_loss": 0.99, "brier": 0.59})
    assert not promotion_allowed(champion, {"log_loss": 0.99, "brier": 0.61})
    assert not promotion_allowed(champion, {"log_loss": 1.01, "brier": 0.59})
    assert not promotion_allowed(champion, {"log_loss": float("nan"), "brier": 0.59})
