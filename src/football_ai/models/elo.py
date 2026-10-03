"""Learn a three-outcome mapping of the historical Elo difference."""

import numpy as np
from sklearn.linear_model import LogisticRegression

from football_ai.models.base import normalize


class EloModel:
    def fit(self, features, matches):
        self.model = LogisticRegression(C=1, max_iter=500)
        self.model.fit(self._inputs(features), [m.outcome for m in matches])
        return self

    @staticmethod
    def _inputs(features):
        difference = features.elo_difference.to_numpy() / 400
        return np.column_stack([difference, np.abs(difference)])

    def predict_proba(self, features, matches):
        output = np.full((len(features), 3), 1e-12)
        output[:, self.model.classes_] = self.model.predict_proba(self._inputs(features))
        return normalize(output)
