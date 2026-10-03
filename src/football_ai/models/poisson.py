"""Regularized, time-weighted football goal model with optional Dixon–Coles.

log(lambda_home) = intercept + home advantage + home attack + away defence.
Attack coefficients are centered for identifiability. Unknown clubs use zero
effects (the learned league prior), not fabricated historical statistics.
"""

import numpy as np
from scipy.optimize import minimize
from scipy.special import gammaln
from scipy.stats import poisson

from football_ai.models.base import normalize


def score_grid(home_rate: float, away_rate: float, rho: float = 0.0) -> np.ndarray:
    if not (0 < home_rate < 100 and 0 < away_rate < 100):
        raise ValueError("Goal rates outside numerical limits")
    maximum = max(8, int(poisson.ppf(1 - 1e-12, max(home_rate, away_rate))))
    scores = np.arange(maximum + 1)
    grid = np.outer(poisson.pmf(scores, home_rate), poisson.pmf(scores, away_rate))
    # Bound rho for this fixture so all four low-score correction factors stay positive.
    rho = float(
        np.clip(rho, -0.99 / max(home_rate, away_rate), 0.99 / max(1, home_rate * away_rate))
    )
    grid[0, 0] *= 1 - home_rate * away_rate * rho
    grid[0, 1] *= 1 + home_rate * rho
    grid[1, 0] *= 1 + away_rate * rho
    grid[1, 1] *= 1 - rho
    return grid / grid.sum()


def regions(grid: np.ndarray) -> np.ndarray:
    return np.array([np.tril(grid, -1).sum(), np.trace(grid), np.triu(grid, 1).sum()])


def reconcile_scores(grid: np.ndarray, outcome_probabilities: np.ndarray) -> np.ndarray:
    """Preserve Poisson conditional score shapes while matching ensemble outcomes."""
    indices = np.indices(grid.shape)
    masks = [indices[0] > indices[1], indices[0] == indices[1], indices[0] < indices[1]]
    output = grid.copy()
    for probability, mask in zip(normalize(outcome_probabilities), masks, strict=True):
        output[mask] *= probability / grid[mask].sum()
    return output / output.sum()


class PoissonModel:
    def __init__(self, regularization=0.05, decay_days=365, dixon_coles=False):
        self.regularization, self.decay_days, self.dixon_coles = (
            regularization,
            decay_days,
            dixon_coles,
        )

    def fit(self, features, matches):
        self.teams = {
            team: i
            for i, team in enumerate(
                sorted({m.home_team for m in matches} | {m.away_team for m in matches})
            )
        }
        n = len(self.teams)
        hi = np.array([self.teams[m.home_team] for m in matches])
        ai = np.array([self.teams[m.away_team] for m in matches])
        hg = np.array([m.home_goals for m in matches], dtype=float)
        ag = np.array([m.away_goals for m in matches], dtype=float)
        latest = max(m.kickoff for m in matches)
        age = np.array([(latest - m.kickoff).total_seconds() / 86400 for m in matches])
        weights = np.exp(-age / self.decay_days)

        def objective(theta):
            attack = theta[2 : 2 + n] - theta[2 : 2 + n].mean()
            defence = theta[2 + n : 2 + 2 * n]
            lh = np.exp(theta[0] + theta[1] + attack[hi] + defence[ai])
            la = np.exp(theta[0] + attack[ai] + defence[hi])
            losses = lh - hg * np.log(lh) + gammaln(hg + 1) + la - ag * np.log(la) + gammaln(ag + 1)
            if self.dixon_coles:
                rho = theta[-1]
                tau = np.ones(len(matches))
                tau[(hg == 0) & (ag == 0)] = (1 - lh * la * rho)[(hg == 0) & (ag == 0)]
                tau[(hg == 0) & (ag == 1)] = (1 + lh * rho)[(hg == 0) & (ag == 1)]
                tau[(hg == 1) & (ag == 0)] = (1 + la * rho)[(hg == 1) & (ag == 0)]
                tau[(hg == 1) & (ag == 1)] = 1 - rho
                if (tau <= 0).any():
                    return 1e6 + float(np.square(np.minimum(tau, 0)).sum())
                losses -= np.log(tau)
            penalty = self.regularization * (np.square(attack).sum() + np.square(defence).sum())
            return float(np.average(losses, weights=weights) + penalty)

        theta = np.zeros(2 + 2 * n + int(self.dixon_coles))
        theta[0] = np.log(max(0.2, ag.mean()))
        theta[1] = np.log(max(0.2, hg.mean()) / max(0.2, ag.mean()))
        bounds = [(-1.5, 1.5), (-0.5, 0.7)] + [(-1.5, 1.5)] * (2 * n)
        if self.dixon_coles:
            bounds += [(-0.1, 0.1)]
        result = minimize(
            objective, theta, method="L-BFGS-B", bounds=bounds, options={"maxiter": 400}
        )
        if not result.success:
            raise RuntimeError(f"Poisson optimization failed: {result.message}")
        self.theta = result.x
        return self

    def rates(self, matches):
        n = len(self.teams)
        attack = self.theta[2 : 2 + n] - self.theta[2 : 2 + n].mean()
        defence = self.theta[2 + n : 2 + 2 * n]
        output = []
        for match in matches:
            hi, ai = self.teams.get(match.home_team), self.teams.get(match.away_team)
            ha, hd = (attack[hi], defence[hi]) if hi is not None else (0, 0)
            aa, ad = (attack[ai], defence[ai]) if ai is not None else (0, 0)
            output.append(
                [np.exp(self.theta[0] + self.theta[1] + ha + ad), np.exp(self.theta[0] + aa + hd)]
            )
        return np.array(output)

    def grids(self, matches):
        rho = self.theta[-1] if self.dixon_coles else 0
        return [score_grid(home, away, rho) for home, away in self.rates(matches)]

    def predict_proba(self, features, matches):
        return normalize(np.array([regions(grid) for grid in self.grids(matches)]))
