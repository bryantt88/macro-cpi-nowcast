"""Point-in-time feature construction (Stage 3 stub).

Every feature is stamped as-of the RELEASE date of its inputs, never the reference date,
so a training row for month T only contains what was knowable before T's CPI was published.

Planned defaults (curated ~15-30, NOT an exhaustive cross-product — see roadmap guardrail):
  - target lags (persistence/momentum)
  - CPI MoM (change) AND CPI YoY (the inflation LEVEL/regime; raw index level excluded)
  - MoM changes of energy inputs (gasoline, WTI, Henry Hub), PPI, food
  - ISM prices-paid / diffusion, 10y-2y slope, real-fed-funds proxy
  - 12/24m rolling z-scores
"""
from __future__ import annotations

import pandas as pd


def build_features(as_of: pd.Timestamp | None = None) -> pd.DataFrame:
    """Assemble the point-in-time feature matrix from the observations store. (Stage 3)"""
    raise NotImplementedError("Feature engineering lands in Stage 3.")
