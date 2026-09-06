"""Point-in-time feature construction (Stage 3).

Builds a monthly feature matrix to nowcast CPI MoM one month ahead. The forecast for
reference month M is treated as made at the END of month M (before the M+1 CPI release):

  * MARKET series (WTI, gasoline, nat-gas, DXY, yields) — daily/weekly, so month-M
    aggregates are fully observed by end-of-M. These are the real-time edge: used at
    month M itself.
  * REVISED macro series (CPI, PPI, PCE, payrolls, unemployment, retail, IndPro) — used
    as the latest FIRST-PRINT value actually released by end-of-M (naturally the M-1
    print). Enforced with a merge_asof on release_date, so nothing leaks backward.
  * Food index — lagged one month (published a few days into M+1); conservative.

Target y(M) = first-print CPI MoM % for month M (the label, revealed at the M+1 release).
Persistence baseline == cpi_mom_lag1. Curated ~18 features (roadmap guardrail: no
exhaustive cross-product). CPI YoY is included as the inflation LEVEL/regime; the raw
index level is deliberately excluded (non-stationary).
"""
from __future__ import annotations

import pandas as pd
from sqlalchemy import Engine

from macro_nowcast import config
from macro_nowcast.db.session import make_engine


def load_observations(engine: Engine) -> pd.DataFrame:
    """Load the tidy long store into a DataFrame with parsed dates."""
    df = pd.read_sql("SELECT series_id, obs_date, value, release_date FROM observations", engine)
    df["obs_date"] = pd.to_datetime(df["obs_date"])
    df["release_date"] = pd.to_datetime(df["release_date"])
    return df


def _series(df: pd.DataFrame, sid: str) -> pd.DataFrame:
    """Return one series' rows, sorted by observation date."""
    return df[df["series_id"] == sid].sort_values("obs_date").reset_index(drop=True)


def _monthly_mom(df: pd.DataFrame, sid: str) -> pd.Series:
    """Month-start MoM %% change of a daily/weekly series' monthly mean (known within-month)."""
    s = _series(df, sid).set_index("obs_date")["value"].resample("MS").mean()
    return s.pct_change() * 100.0


def asof_known(block: pd.DataFrame, cutoffs: pd.DatetimeIndex, cols: list[str]) -> pd.DataFrame:
    """For each cutoff, return the most recent block row already RELEASED (<= cutoff).

    `block` is indexed by obs_date and must carry a 'release_date' column. This is the
    no-look-ahead join: a value is visible only on/after its release date.
    """
    right = block.reset_index().rename(columns={block.index.name or "index": "obs_date"})
    right = right[["release_date", *cols]].sort_values("release_date")
    left = pd.DataFrame({"cutoff": pd.DatetimeIndex(cutoffs)}).sort_values("cutoff")
    merged = pd.merge_asof(left, right, left_on="cutoff", right_on="release_date", direction="backward")
    out = merged[cols]
    out.index = left["cutoff"].to_numpy()
    return out


def _pit_block(df: pd.DataFrame, sid: str, transform: str) -> pd.DataFrame:
    """First-print MoM/level block for a revised macro series, keyed by obs_date + release_date."""
    s = _series(df, sid).set_index("obs_date")
    val = s["value"]
    block = pd.DataFrame(index=s.index)
    block["release_date"] = s["release_date"].to_numpy()
    if transform == "mom":
        block["v"] = (val.pct_change() * 100.0).to_numpy()
        block["v1"] = (val.pct_change() * 100.0).shift(1).to_numpy()
        block["v2"] = (val.pct_change() * 100.0).shift(2).to_numpy()
        block["yoy"] = (val.pct_change(12) * 100.0).to_numpy()
    elif transform == "level":
        block["v"] = val.to_numpy()
    return block


def build_features(engine: Engine | None = None, model_start: str | None = None) -> pd.DataFrame:
    """Assemble the point-in-time feature matrix (index = reference month, plus 'target')."""
    engine = engine or make_engine()
    df = load_observations(engine)
    start = pd.Timestamp(model_start or config.MODEL_START)

    # Reference grid: every month for which a first-print CPI MoM (target) exists.
    cpi = _series(df, "CPIAUCSL").set_index("obs_date")["value"]
    cpi_mom = (cpi.pct_change() * 100.0)
    grid = pd.DatetimeIndex(cpi_mom.index)  # month-start timestamps (reference month M)
    # Forecast is made at END of month M: month-M market data is in, and CPI(M-1)/PPI(M-1)
    # etc. have been released (mid-M), but CPI(M) has not. This is the no-look-ahead cutoff.
    cutoffs = grid + pd.offsets.MonthEnd(0)
    feats = pd.DataFrame(index=grid)

    # --- Target: first-print CPI MoM for month M (the label) ----------------------
    feats["target"] = cpi_mom.to_numpy()

    # --- CPI history known as-of end-of-M (persistence + momentum + level/regime) --
    cpi_block = _pit_block(df, "CPIAUCSL", "mom")
    known = asof_known(cpi_block, cutoffs, ["v", "v1", "v2", "yoy"])
    feats["cpi_mom_lag1"] = known["v"].to_numpy()   # == persistence baseline
    feats["cpi_mom_lag2"] = known["v1"].to_numpy()
    feats["cpi_mom_lag3"] = known["v2"].to_numpy()
    feats["cpi_yoy_lag1"] = known["yoy"].to_numpy()  # inflation LEVEL / regime
    feats["cpi_mom_z24"] = (
        (feats["cpi_mom_lag1"] - feats["cpi_mom_lag1"].rolling(24, min_periods=12).mean())
        / feats["cpi_mom_lag1"].rolling(24, min_periods=12).std()
    )

    # --- Real-time market edge: month-M aggregates (known by end-of-M) -------------
    feats["wti_mom"] = _monthly_mom(df, "WTI").reindex(grid).to_numpy()
    feats["gasoline_mom"] = _monthly_mom(df, "GASREGW").reindex(grid).to_numpy()
    feats["natgas_mom"] = _monthly_mom(df, "DHHNGSP").reindex(grid).to_numpy()
    feats["dxy_mom"] = _monthly_mom(df, "DXY").reindex(grid).to_numpy()

    # 10y-2y slope (context), month-M average level
    slope = (
        _series(df, "DGS10").set_index("obs_date")["value"].resample("MS").mean()
        - _series(df, "DGS2").set_index("obs_date")["value"].resample("MS").mean()
    )
    feats["slope_10y2y"] = slope.reindex(grid).to_numpy()

    # --- Pipeline / cost: latest first-print MoM known as-of end-of-M --------------
    for sid, name in [("PPIACO", "ppi_mom_lag1"), ("PAYEMS", "payems_mom_lag1"),
                      ("RSAFS", "retail_mom_lag1"), ("PPIFIS", "ppifis_mom_lag1")]:
        blk = _pit_block(df, sid, "mom")
        feats[name] = asof_known(blk, cutoffs, ["v"])["v"].to_numpy()

    # Unemployment level, latest first-print known
    unrate = _pit_block(df, "UNRATE", "level")
    feats["unrate_lag1"] = asof_known(unrate, cutoffs, ["v"])["v"].to_numpy()

    # Prices-paid diffusion surveys (ISM substitute), released within month M -> level
    for sid, name in [("PPCDFSA066MSFRBPHI", "phil_pricespaid"), ("PPCDISA066MSFRBNY", "ny_pricespaid")]:
        s = _series(df, sid).set_index("obs_date")["value"].resample("MS").mean()
        feats[name] = s.reindex(grid).to_numpy()

    # Food commodity index: lag one month (publishes a few days into M+1) -> conservative
    food_mom = (_series(df, "PFOODINDEXM").set_index("obs_date")["value"].pct_change() * 100.0)
    feats["food_mom_lag1"] = food_mom.reindex(grid).shift(1).to_numpy()

    return feats.loc[feats.index >= start].copy()
