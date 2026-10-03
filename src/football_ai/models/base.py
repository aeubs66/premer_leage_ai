"""Model contract. Class order is always HOME, DRAW, AWAY."""

from typing import Protocol

import numpy as np
import pandas as pd

from football_ai.data.schemas import Match


def normalize(probabilities: np.ndarray) -> np.ndarray:
    probabilities = np.asarray(probabilities, dtype=float)
    if not np.isfinite(probabilities).all() or (probabilities < 0).any():
        raise ValueError("Model returned invalid probabilities")
    probabilities = np.maximum(probabilities, 1e-12)
    return probabilities / probabilities.sum(axis=-1, keepdims=True)


class OutcomeModel(Protocol):
    def fit(self, features: pd.DataFrame, matches: list[Match]) -> "OutcomeModel": ...
    def predict_proba(self, features: pd.DataFrame, matches: list[Match]) -> np.ndarray: ...
