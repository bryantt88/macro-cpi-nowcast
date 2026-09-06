"""Central configuration: paths, target spec, and the locked input series catalog.

Everything tunable lives here (or in `.env`) — no magic numbers or hardcoded paths
scattered through the code. The series catalog is DATA, not logic, so adding/removing
an indicator is a one-line edit here, never a code change downstream.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # read .env if present; real secrets never live in this file

# --- Paths (all relative to the project root, resolved absolutely) ---------------
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
DATA_DIR: Path = PROJECT_ROOT / "data"
REPORTS_DIR: Path = PROJECT_ROOT / "reports"
DB_PATH: Path = Path(os.getenv("MACRO_DB_PATH", DATA_DIR / "macro.db"))


# --- Target spec (config-swappable per the locked roadmap) -----------------------
@dataclass(frozen=True)
class TargetSpec:
    """What we forecast. Swap `series_id` to nowcast core CPI / PCE / etc. later."""

    series_id: str = os.getenv("MACRO_TARGET_SERIES", "CPIAUCSL")  # US headline CPI
    transform: str = "mom_pct"          # predict month-over-month % change
    horizon_months: int = int(os.getenv("MACRO_FORECAST_HORIZON", "1"))  # 1 month ahead


TARGET = TargetSpec()


# --- Input series catalog (LOCKED 2026-09-07) ------------------------------------
# role: "target" | "primary" (in the CPI basket / real-time edge) | "context" (demoted,
#       kept but down-weighted — see reference-rates-endogeneity note).
@dataclass(frozen=True)
class Series:
    """One input indicator and where/how to fetch it."""

    series_id: str        # FRED code or market ticker
    source: str           # "FRED" | "YFINANCE" | "TREASURY"
    description: str
    frequency: str        # "D" | "W" | "M"
    role: str             # "target" | "primary" | "context"


CATALOG: list[Series] = [
    # --- Target -------------------------------------------------------------------
    Series("CPIAUCSL", "FRED", "US headline CPI, all items, SA (target)", "M", "target"),
    # --- Primary: mechanically inside the CPI basket / real-time energy edge -------
    Series("GASREGW",  "FRED", "US retail gasoline price, regular, weekly", "W", "primary"),
    Series("PPIACO",   "FRED", "Producer Price Index, all commodities", "M", "primary"),
    Series("PPIFIS",   "FRED", "PPI final demand", "M", "primary"),
    Series("PFOODINDEXM", "FRED", "Global food commodity price index", "M", "primary"),
    Series("DHHNGSP",  "FRED", "Henry Hub natural gas spot price", "D", "primary"),
    Series("PCEPI",    "FRED", "PCE price index (cross-check inflation gauge)", "M", "primary"),
    Series("PAYEMS",   "FRED", "Nonfarm payrolls", "M", "primary"),
    Series("UNRATE",   "FRED", "Unemployment rate", "M", "primary"),
    Series("NAPM",     "FRED", "ISM Manufacturing PMI", "M", "primary"),
    Series("RSAFS",    "FRED", "Advance retail sales", "M", "primary"),
    Series("WTISPLC",  "FRED", "WTI crude oil spot (monthly avg)", "M", "primary"),
    Series("WTI",      "YFINANCE", "WTI crude front-month (CL=F), daily real-time", "D", "primary"),
    Series("DXY",      "YFINANCE", "US dollar index (DX-Y.NYB), daily", "D", "primary"),
    # --- Context: DEMOTED (kept in store, down-weighted downstream) ---------------
    Series("INDPRO",   "FRED", "Industrial production (context)", "M", "context"),
    Series("FEDFUNDS", "FRED", "Effective fed funds rate (context; circular)", "M", "context"),
    Series("DGS2",     "FRED", "2-year Treasury yield (context; circular)", "D", "context"),
    Series("DGS10",    "FRED", "10-year Treasury yield (context; circular)", "D", "context"),
    Series("SPY",      "YFINANCE", "S&P 500 ETF (context; financial conditions)", "D", "context"),
    Series("GOLD",     "YFINANCE", "Gold front-month (GC=F) (context)", "D", "context"),
]


# --- Backtest / validation knobs (used from Stage 4; defined here to avoid magic
#     numbers later). Values are placeholders to be reviewed when Stage 4 lands. ---
@dataclass(frozen=True)
class BacktestConfig:
    """Expanding walk-forward settings. Baseline = persistence (carry last MoM)."""

    min_train_months: int = 120     # first fold trains on >= this many months
    baseline: str = "persistence"   # locked: "next MoM = this MoM" (NOT 0%/level walk)


BACKTEST = BacktestConfig()


def fred_api_key() -> str | None:
    """Return the FRED API key from the environment, or None if unset (Stage 2 checks this)."""
    return os.getenv("FRED_API_KEY") or None
