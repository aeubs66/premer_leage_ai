"""Margin-removed decimal odds for probability benchmarking, not betting."""

import numpy as np


def implied_probabilities(home: float, draw: float, away: float):
    odds = np.array([home, draw, away], dtype=float)
    if not np.isfinite(odds).all() or (odds <= 1).any():
        raise ValueError("Decimal odds must be finite and greater than one")
    implied = 1 / odds
    return {
        "probabilities": (implied / implied.sum()).tolist(),
        "overround": float(implied.sum() - 1),
        "method": "proportional margin removal",
    }
