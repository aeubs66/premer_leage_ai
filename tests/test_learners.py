import joblib
import numpy as np
from test_data import match

from football_ai.config import Settings
from football_ai.features.pipeline import FeaturePipeline
from football_ai.models.boosting import BoostingModel
from football_ai.models.neural import NeuralModel


def test_training_only_imputation_and_boost_serialization(tmp_path):
    matches = [match(i, hg=i % 3, ag=1) for i in range(60)]
    frame = FeaturePipeline(Settings().load("features")).transform(matches)
    first = BoostingModel({"n_estimators": 10, "max_depth": 2}).fit(frame.iloc[:45], matches[:45])
    median = first.imputer.statistics_.copy()
    changed = frame.iloc[45:].copy()
    changed["home_gf_5"] = 10000
    first.predict_proba(changed, matches[45:])
    np.testing.assert_array_equal(first.imputer.statistics_, median)
    joblib.dump(first, tmp_path / "tree.joblib")
    np.testing.assert_allclose(
        joblib.load(tmp_path / "tree.joblib").predict_proba(frame.iloc[45:], matches[45:]),
        first.predict_proba(frame.iloc[45:], matches[45:]),
    )


def test_neural_reproducibility_and_unknown_teams(tmp_path):
    matches = [match(i, hg=i % 3, ag=1) for i in range(60)]
    frame = FeaturePipeline(Settings().load("features")).transform(matches)
    first = NeuralModel(width=8, epochs=3).fit(frame.iloc[:50], matches[:50])
    second = NeuralModel(width=8, epochs=3).fit(frame.iloc[:50], matches[:50])
    probabilities = first.predict_proba(frame.iloc[50:], matches[50:])
    np.testing.assert_allclose(
        probabilities, second.predict_proba(frame.iloc[50:], matches[50:]), atol=1e-7
    )
    joblib.dump(first, tmp_path / "neural.joblib")
    np.testing.assert_allclose(
        probabilities,
        joblib.load(tmp_path / "neural.joblib").predict_proba(frame.iloc[50:], matches[50:]),
        atol=1e-7,
    )
