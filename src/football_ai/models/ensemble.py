"""Fit meta-models only on time-aware out-of-fold base predictions."""

import numpy as np
from scipy.optimize import minimize
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier

from football_ai.models.base import normalize


class Ensemble:
    def __init__(self, kind="weighted", names=None, seed=42):
        self.kind, self.names, self.seed = kind, names or [], seed

    def matrix(self, predictions):
        # Log probabilities provide a compact, interpretable stacking input.
        return np.concatenate([np.log(np.maximum(predictions[name], 1e-12)) for name in self.names], axis=1)

    def fit(self, predictions, targets):
        targets = np.asarray(targets, dtype=int)
        if self.kind == "single":
            return self
        if self.kind == "weighted":
            tensor = np.stack([predictions[name] for name in self.names], axis=1)

            def loss(weights):
                blended = np.einsum("nmc,m->nc", tensor, weights)
                return float(-np.log(np.maximum(blended[np.arange(len(targets)), targets], 1e-12)).mean() + 0.005 * np.square(weights).sum())

            result = minimize(loss, np.ones(len(self.names)) / len(self.names), method="SLSQP",
                              bounds=[(0, 1)] * len(self.names), constraints={"type": "eq", "fun": lambda w: w.sum() - 1})
            if not result.success:
                raise RuntimeError(f"Ensemble optimization failed: {result.message}")
            self.weights = np.maximum(result.x, 0)
            self.weights /= self.weights.sum()
        else:
            self.model = LogisticRegression(C=0.1, max_iter=1000) if self.kind == "logistic" else MLPClassifier(hidden_layer_sizes=(8,), alpha=10, max_iter=500, solver="lbfgs", random_state=self.seed)
            self.model.fit(self.matrix(predictions), targets)
        return self

    def predict_proba(self, predictions):
        if self.kind == "single":
            return normalize(predictions[self.names[0]])
        if self.kind == "weighted":
            return normalize(sum(w * predictions[name] for w, name in zip(self.weights, self.names, strict=True)))
        output = np.full((len(next(iter(predictions.values()))), 3), 1e-12)
        output[:, self.model.classes_] = self.model.predict_proba(self.matrix(predictions))
        return normalize(output)
