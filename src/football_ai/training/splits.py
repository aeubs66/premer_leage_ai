"""Sealed seasons and expanding-window folds, never random partitions."""

from collections import Counter
from datetime import UTC, datetime

import numpy as np


def season_split(matches):
    counts = Counter(m.season for m in matches)
    now = datetime.now(UTC)
    current_start = now.year if now.month >= 7 else now.year - 1
    completed = sorted(
        season for season, n in counts.items() if n >= 380 and int(season[:4]) < current_start
    )
    if not completed:
        raise ValueError("Need at least one complete 380-match season for a sealed final test")
    test_season = completed[-1]
    pretest = [i for i, m in enumerate(matches) if m.season < test_season]
    test = [i for i, m in enumerate(matches) if m.season == test_season]
    prospective = [i for i, m in enumerate(matches) if m.season > test_season]
    if len(pretest) < 760:
        raise ValueError(
            "Need at least two earlier seasons for training and chronological validation"
        )
    return pretest, test, prospective, test_season


def walk_folds(matches, warmup=380, blocks=6):
    days = sorted({m.kickoff.date() for m in matches})
    first = next(
        (i for i, day in enumerate(days) if sum(m.kickoff.date() < day for m in matches) >= warmup),
        None,
    )
    if first is None or len(days[first:]) < blocks:
        raise ValueError("Not enough chronological days for walk-forward validation")
    for block in np.array_split(np.array(days[first:], dtype=object), blocks):
        start, end = block[0], block[-1]
        cutoff = min(m.kickoff for m in matches if m.kickoff.date() == start)
        train = [i for i, m in enumerate(matches) if m.result_available_at < cutoff]
        validation = [i for i, m in enumerate(matches) if start <= m.kickoff.date() <= end]
        yield train, validation


def meta_partitions(matches):
    # Boundaries move to whole days so simultaneous fixtures never cross stages.
    dates = np.array([m.kickoff.date() for m in matches])
    middle = dates[len(matches) // 2]
    last = dates[3 * len(matches) // 4]
    fit = np.flatnonzero(dates < middle)
    calibration = np.flatnonzero((dates >= middle) & (dates < last))
    selection = np.flatnonzero(dates >= last)
    if min(len(fit), len(calibration), len(selection)) < 40:
        raise ValueError("Too few independent meta/calibration/selection samples")
    return fit, calibration, selection
