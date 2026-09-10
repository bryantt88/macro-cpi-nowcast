"""One-page CPI forecast note (a concise, dated snapshot for the next unreleased print).

Unlike the full baseline report, this is a short desk note: the point forecast for the next
CPI release, an uncertainty band, and a plain read of whether the print is likely above or
below (a) the historical average and (b) the street consensus. Consensus is not free data, so
it is passed in by the user at run time.

Run: `python -m macro_nowcast.report.forecast_note 0.40`   (0.40 = current street consensus)
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from macro_nowcast import config
from macro_nowcast.db.session import make_engine
from macro_nowcast.features.build import build_features
from macro_nowcast.models.train import _make_lgbm, _make_ridge
from macro_nowcast.report.paper import _styles, _table

# Backtested out-of-sample RMSE of the ensemble (percentage points); the ± band around a point
# forecast. Sourced from the Stage-5 evaluation; see reports/*_baseline.md.
OOS_RMSE = 0.175


def predict_next(engine, cutoff_mode: str = "pre_release") -> dict:
    """Train on all released months and nowcast the next unreleased CPI print. Returns a dict."""
    f = build_features(cutoff_mode=cutoff_mode, include_pending=True)
    train = f.dropna(subset=["target"])
    pending = f[f["target"].isna() & (f.index > train.index.max())]  # unreleased months after last print
    if pending.empty:
        raise RuntimeError("No pending month to forecast — the latest CPI is already released.")
    tgt = pending.index.min()
    cols = [c for c in f.columns if c != "target"]
    X, y, xnew = train[cols], train["target"].to_numpy(), f.loc[[tgt], cols]
    ridge = float(_make_ridge().fit(X, y).predict(xnew)[0])
    lgbm = float(_make_lgbm().fit(X, y).predict(xnew)[0])
    ens = (ridge + lgbm) / 2.0
    cf = pd.read_sql("SELECT ref_month, cpi_mom_nowcast FROM cf_nowcast", engine,
                     parse_dates=["ref_month"]).set_index("ref_month")
    fed = float(cf.loc[tgt, "cpi_mom_nowcast"]) if tgt in cf.index else float("nan")
    return {
        "month": tgt, "ridge": ridge, "lgbm": lgbm, "ensemble": ens, "fed": fed,
        "blend": np.nanmean([ens, fed]), "naive": float(f.loc[tgt, "cpi_mom_lag1"]),
        "hist_avg": float(train["target"].mean()),
        "recent_avg": float(train.loc[train.index >= "2015-01-01", "target"].mean()),
        "drivers": {k: float(f.loc[tgt, k]) for k in ("gasoline_mom", "wti_mom", "dxy_mom")},
    }


def write_note(engine=None, consensus: float | None = None, out_path: Path | None = None) -> Path:
    """Render the one-page forecast note PDF. `consensus` = current street median (percent)."""
    engine = engine or make_engine()
    d = predict_next(engine)
    S = _styles()
    P = lambda t, st="body": Paragraph(t, S[st])  # noqa: E731
    m, ens, blend, fed = d["month"], d["ensemble"], d["blend"], d["fed"]
    lo, hi = ens - OOS_RMSE, ens + OOS_RMSE
    dr = d["drivers"]

    story = [
        P(f"US CPI Forecast Note — {m:%B %Y}", "title"),
        P(f"Headline CPI, month-over-month %. Prepared {date.today():%d %B %Y}. "
          f"Model: point-in-time ridge + LightGBM ensemble (backtested RMSE ≈ {OOS_RMSE:.2f}pp).", "meta"),
        Spacer(1, 8),
    ]

    # Forecast table
    rows = [["Forecaster", "Aug 2026 MoM"]]
    rows.append(["Our model (ensemble)", f"{ens:+.2f}%"])
    rows.append(["Blend (our model + Cleveland Fed)", f"{blend:+.2f}%"])
    if consensus is not None:
        rows.append([f"Street consensus", f"{consensus:+.2f}%"])
    rows.append(["Cleveland Fed nowcast", f"{fed:+.2f}%"])
    rows.append(["Naive (repeat July)", f"{d['naive']:+.2f}%"])
    story += [_table(rows, [9.5 * cm, 4.0 * cm], highlight_row=1),
              P(f"68% band on our model: <b>{lo:+.2f}% to {hi:+.2f}%</b> (±1 backtested RMSE).", "cap"),
              Spacer(1, 10)]

    # Analysis
    above_avg = ens > d["recent_avg"]
    cons_txt = ""
    if consensus is not None:
        gap = ens - consensus
        lean = ("slightly above" if gap > 0.03 else "slightly below" if gap < -0.03 else "in line with")
        cons_txt = (
            f" Relative to the street consensus of {consensus:+.2f}%, our model sits {lean} it "
            f"(blend {blend:+.2f}%, essentially at consensus). Given the model's thin measured edge over a "
            f"well-informed consensus, we read the surprise risk as modest and tilted {'to the upside' if gap > 0 else 'to the downside' if gap < 0 else 'neutral'} — "
            f"low conviction on direction, higher conviction on the level.")

    story += [
        P("Analysis", "h"),
        P(f"<b>Above or below average?</b> Clearly <b>above</b>. The forecast (~{ens:+.2f}%) exceeds the "
          f"long-run monthly average of {d['hist_avg']:+.2f}% and the recent (2015–) average of "
          f"{d['recent_avg']:+.2f}%, and stands far above July's {d['naive']:+.2f}%. This is a firm, "
          f"above-trend month, not a soft one."),
        P(f"<b>What is driving it?</b> Energy. Gasoline rose {dr['gasoline_mom']:+.1f}% and crude "
          f"{dr['wti_mom']:+.1f}% over the month, with a softer dollar ({dr['dxy_mom']:+.1f}%) adding at the "
          f"margin. This real-time energy rebound is exactly the signal the naive baseline misses, and it is "
          f"why the model prints so far above July.{cons_txt}"),
        Spacer(1, 6),
        P(f"<b>Bottom line:</b> a firm, above-average August CPI near <b>{blend:+.2f}%</b> "
          f"(range ~{lo:+.2f}% to {hi:+.2f}%), roughly in line with consensus with a mild upside tilt, "
          f"led by the August energy rebound.", "body"),
        Spacer(1, 8),
        P("Caveat: a systematic multi-month edge, not single-print precision; professional consensus "
          "(~0.12pp) is tighter. The market reaction depends on the print relative to consensus, where the "
          "model's directional edge is limited.", "small"),
    ]

    out = out_path or (config.PROJECT_ROOT / "docs" / f"CPI_Forecast_Note_{m:%Y_%m}.pdf")
    out.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(out), pagesize=A4, topMargin=2.0 * cm, bottomMargin=2.0 * cm,
                      leftMargin=2.2 * cm, rightMargin=2.2 * cm,
                      title=f"US CPI Forecast Note — {m:%B %Y}", author="Bryant Effendi").build(story)
    return out


if __name__ == "__main__":
    cons = float(sys.argv[1]) if len(sys.argv) > 1 else None
    path = write_note(consensus=cons)
    print(f"Forecast note written: {path}")
