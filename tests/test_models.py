import joblib
import numpy as np
import pytest

from football_ai.config import Settings
from football_ai.features.pipeline import FeaturePipeline
from football_ai.models.baseline import Baseline
from football_ai.models.elo import EloModel
from football_ai.models.poisson import PoissonModel, reconcile_scores, regions, score_grid
from test_data import match


def test_score_distribution_and_tail():
    for home, away in [(0.2, 0.4), (1.8, 1.4), (8, 9)]:
        grid = score_grid(home, away)
        assert grid.sum() == pytest.approx(1)
        assert (grid >= 0).all()
        reconciled = reconcile_scores(grid, np.array([0.4, 0.3, 0.3]))
        np.testing.assert_allclose(regions(reconciled), [0.4, 0.3, 0.3], atol=1e-12)
        if home > 8:
            assert grid.shape[0] > 9


@pytest.mark.parametrize("model", [Baseline(), EloModel(), PoissonModel(), PoissonModel(dixon_coles=True)])
def test_models_and_serialization(model, tmp_path):
    records = [match(i, hg=i % 3, ag=(i + 1) % 3) for i in range(30)]
    features = FeaturePipeline(Settings().load("features")).transform(records)
    model.fit(features.iloc[:25], records[:25])
    probabilities = model.predict_proba(features.iloc[25:], records[25:])
    np.testing.assert_allclose(probabilities.sum(axis=1), 1)
    path = tmp_path / "model.joblib"
    joblib.dump(model, path)
    np.testing.assert_allclose(joblib.load(path).predict_proba(features.iloc[25:], records[25:]), probabilities)
