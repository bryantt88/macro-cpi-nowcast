"""Expanding-window walk-forward training + scoring (Stage 4 stub).

Models: ridge + shallow LightGBM (regularized to absorb many correlated inputs).
Validation: expanding walk-forward ONLY (no k-fold, no look-ahead). Metrics: OOS RMSE,
MAE, directional accuracy, hit-rate vs the persistence baseline. Reports fold-by-fold,
and states plainly if it does NOT beat naive.
"""
from __future__ import annotations

import pandas as pd


def walk_forward_eval(features: pd.DataFrame, target: pd.Series) -> dict:
    """Run expanding walk-forward, returning fold-by-fold + aggregate metrics. (Stage 4)"""
    raise NotImplementedError("Walk-forward training lands in Stage 4.")
