"""The no-look-ahead invariant: asof_known never returns a value before it was released."""
from __future__ import annotations

import pandas as pd

from macro_nowcast.features.build import asof_known


def test_asof_respects_release_date() -> None:
    """A value released in month M+1 must NOT be visible at the end of month M."""
    # Three monthly obs; each released ~6 weeks after its reference month.
    block = pd.DataFrame(
        {
            "release_date": pd.to_datetime(["2020-02-15", "2020-03-15", "2020-04-15"]),
            "v": [1.0, 2.0, 3.0],
        },
        index=pd.to_datetime(["2020-01-01", "2020-02-01", "2020-03-01"]),  # obs months
    )
    cutoffs = pd.to_datetime(["2020-02-29", "2020-03-31", "2020-04-30"])  # end-of-month forecasts

    got = asof_known(block, cutoffs, ["v"])["v"].tolist()

    # End of Feb: only Jan's value (released Feb 15) is known -> 1.0, NOT Feb's (released Mar 15).
    # End of Mar: Feb's value (released Mar 15) -> 2.0.  End of Apr: Mar's value -> 3.0.
    assert got == [1.0, 2.0, 3.0]


def test_asof_returns_nan_before_first_release() -> None:
    """Before anything is released, there is no known value."""
    block = pd.DataFrame(
        {"release_date": pd.to_datetime(["2020-03-15"]), "v": [5.0]},
        index=pd.to_datetime(["2020-02-01"]),
    )
    got = asof_known(block, pd.to_datetime(["2020-02-29"]), ["v"])["v"]
    assert got.isna().all()
