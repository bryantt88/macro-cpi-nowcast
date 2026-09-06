"""Unit test for the persistence baseline (the benchmark every model must beat)."""
from __future__ import annotations

import pandas as pd

from macro_nowcast.models.baseline import persistence_forecast


def test_persistence_carries_prior_value() -> None:
    """Each forecast equals the previous period's MoM; first entry is NaN."""
    mom = pd.Series([0.2, 0.3, 0.5], index=pd.to_datetime(["2026-01-01", "2026-02-01", "2026-03-01"]))
    fc = persistence_forecast(mom)
    assert pd.isna(fc.iloc[0])
    assert fc.iloc[1] == 0.2
    assert fc.iloc[2] == 0.3
