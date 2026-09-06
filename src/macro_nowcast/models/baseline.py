"""The naive baseline the model must beat: PERSISTENCE (locked).

'Next month's MoM = this month's MoM.' NOT the 0%/level random walk. Implemented now
because it needs no training data and anchors every score from Stage 4 onward.
"""
from __future__ import annotations

import pandas as pd


def persistence_forecast(mom_history: pd.Series) -> pd.Series:
    """Forecast each period's MoM as the previous period's MoM (carry-forward, shift by 1).

    Args:
        mom_history: time-indexed series of realized MoM % changes.
    Returns:
        Series aligned to `mom_history` where each value is the prior period's MoM
        (first entry is NaN — nothing to carry from).
    """
    if not isinstance(mom_history, pd.Series):
        raise TypeError("mom_history must be a pandas Series indexed by date.")
    return mom_history.shift(1)
