"""Walk-forward mechanics: correct OOS shape, and metrics that behave as defined."""
from __future__ import annotations

import numpy as np
import pandas as pd

from macro_nowcast.models.train import walk_forward_eval


def _toy(n: int = 60) -> pd.DataFrame:
    """Synthetic monthly matrix where target is loosely tied to last month's MoM + a feature."""
    rng = np.random.default_rng(0)
    idx = pd.date_range("2000-01-01", periods=n, freq="MS")
    lag1 = rng.normal(0.3, 0.2, n)
    target = 0.5 * lag1 + 0.1 * rng.normal(0, 0.2, n) + 0.15
    return pd.DataFrame({"target": target, "cpi_mom_lag1": lag1, "feat": rng.normal(0, 1, n)}, index=idx)


def test_walk_forward_shapes_and_keys() -> None:
    """OOS length == n - min_train, and every model reports the metric keys."""
    res = walk_forward_eval(_toy(60), min_train=36)
    assert res["n_oos"] == 60 - 36
    assert set(res["oos"].columns) == {"actual", "persistence", "ridge", "lgbm", "ensemble"}
    for model in ("persistence", "ridge", "lgbm", "ensemble"):
        assert {"rmse", "mae", "dir_acc", "hit_rate", "rmse_skill"} <= res["metrics"][model].keys()


def test_persistence_skill_is_zero_by_definition() -> None:
    """Persistence measured against itself has exactly zero RMSE skill."""
    res = walk_forward_eval(_toy(60), min_train=36)
    assert abs(res["metrics"]["persistence"]["rmse_skill"]) < 1e-12
