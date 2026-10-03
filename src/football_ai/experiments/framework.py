"""Small experiment contract requiring a hypothesis and explicit CPU budget."""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Experiment:
    name: str
    hypothesis: str
    minimum_matches: int
    cpu_budget_seconds: int
    run: Callable

    def execute(self, features, matches):
        if not self.hypothesis.strip() or self.cpu_budget_seconds <= 0:
            raise ValueError("Experiments require a hypothesis and a positive CPU budget")
        if len(matches) < self.minimum_matches:
            raise ValueError("Insufficient data for the registered hypothesis")
        import time

        start = time.perf_counter()
        result = self.run(features, matches)
        elapsed = time.perf_counter() - start
        return {
            "name": self.name,
            "hypothesis": self.hypothesis,
            "elapsed_seconds": elapsed,
            "budget_exceeded": elapsed > self.cpu_budget_seconds,
            "production_eligible": False,
            "result": result,
        }


def monte_carlo_scores(grid, simulations=10000, seed=42):
    """Check simulation error against the exact score distribution; CPU only."""
    if simulations < 1:
        raise ValueError("Simulations must be positive")
    rng = np.random.default_rng(seed)
    outcomes = rng.choice(grid.size, size=simulations, p=grid.ravel())
    empirical = np.bincount(outcomes, minlength=grid.size).reshape(grid.shape) / simulations
    return {
        "simulations": simulations,
        "seed": seed,
        "max_cell_error": float(np.abs(empirical - grid).max()),
        "empirical_grid": empirical.tolist(),
    }
