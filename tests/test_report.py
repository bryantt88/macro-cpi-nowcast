"""Fast unit tests for the report's pure helpers.

We deliberately do NOT run the full report here (it triggers four walk-forward passes and is
slow); those numbers are exercised by test_train. These tests pin the deterministic building
blocks: error math, per-year skill aggregation, and markdown-table rendering.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from macro_nowcast.report.build import _md_table, _per_year_skill, _rmse


def test_rmse_matches_manual() -> None:
    """_rmse is the plain root-mean-square error in pp."""
    pred = np.array([0.1, 0.2, 0.3])
    actual = np.array([0.0, 0.0, 0.0])
    assert _rmse(pred, actual) == float(np.sqrt(np.mean(pred**2)))


def test_per_year_skill_shape_and_sign() -> None:
    """Per-year table has one row per year, and positive skill when the model beats naive."""
    idx = pd.to_datetime(["2020-01-01", "2020-02-01", "2021-01-01"])
    oos = pd.DataFrame(
        {"actual": [0.3, 0.1, 0.2], "ensemble": [0.29, 0.11, 0.21], "persistence": [0.0, 0.0, 0.0]},
        index=idx,
    )
    py = _per_year_skill(oos)
    assert list(py.index) == [2020, 2021]
    assert (py["skill"] > 0).all()  # model is far closer than the all-zero naive here
    assert int(py.loc[2020, "n"]) == 2


def test_md_table_renders_header_and_rows() -> None:
    """_md_table emits a GitHub table with a header, a rule row, and one row per record."""
    df = pd.DataFrame({"year": [2020], "skill": [0.5]})
    md = _md_table(df, {"year": "Year", "skill": "Skill"}, {"year": "{:.0f}", "skill": "{:.1%}"})
    lines = md.splitlines()
    assert lines[0] == "| Year | Skill |"
    assert set(lines[1]) <= {"|", "-"}
    assert lines[2] == "| 2020 | 50.0% |"
