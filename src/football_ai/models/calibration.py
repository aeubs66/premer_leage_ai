"""Separate fitted calibration, including a genuine no-calibration candidate."""

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import softmax
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

from football_ai.models.base import normalize


class Calibrator:
    def __init__(self, kind="none"):
        self.kind = kind

    def fit(self, probabilities, targets):
        probabilities = normalize(probabilities)
        targets = np.asarray(targets, dtype=int)
        if self.kind == "temperature":
            logits = np.log(probabilities)

            def loss(log_temperature):
                prediction = softmax(logits / np.exp(log_temperature), axis=1)
                return float(-np.log(prediction[np.arange(len(targets)), targets]).mean())

            result = minimize_scalar(loss, bounds=(-2, 2), method="bounded")
            self.temperature = float(np.exp(result.x))
        elif self.kind in ("sigmoid", "isotonic"):
            self.models = []
            for label in range(3):
                binary = (targets == label).astype(int)
                if len(np.unique(binary)) < 2:
                    raise ValueError("Calibration block must include all three outcomes")
                model = (
                    LogisticRegression(C=1)
                    if self.kind == "sigmoid"
                    else IsotonicRegression(out_of_bounds="clip", y_min=1e-6, y_max=1 - 1e-6)
                )
                x = (
                    np.log(probabilities[:, label] / (1 - probabilities[:, label])).reshape(-1, 1)
                    if self.kind == "sigmoid"
                    else probabilities[:, label]
                )
                model.fit(x, binary)
                self.models.append(model)
        return self

    def transform(self, probabilities):
        probabilities = normalize(probabilities)
        if self.kind == "none":
            return probabilities
        if self.kind == "temperature":
            return normalize(softmax(np.log(probabilities) / self.temperature, axis=1))
        columns = []
        for label, model in enumerate(self.models):
            if self.kind == "sigmoid":
                x = np.log(probabilities[:, label] / (1 - probabilities[:, label])).reshape(-1, 1)
                columns.append(model.predict_proba(x)[:, 1])
            else:
                columns.append(model.predict(probabilities[:, label]))
        return normalize(np.column_stack(columns))
