"""Cleveland Fed Inflation Nowcast — external benchmark source.

The Cleveland Fed publishes a free daily model nowcast of the current month's CPI/PCE
inflation. It is the right benchmark for THIS project: monthly frequency, headline CPI MoM,
and it runs on the same ingredients we use (daily oil, weekly gasoline, monthly CPI) — so a
head-to-head is apples-to-apples. (SPF is quarterly; economist consensus is paid.)

Data comes from the JSON behind their interactive chart (one file, no scraping, no key):
each entry is one reference month holding the DAILY nowcast path (CPI/Core/PCE/Core-PCE)
plus the realized "Actual" line once released. We keep, per reference month:
  * cpi_mom_nowcast        — the FINAL nowcast (last populated value, ~release day)
  * cpi_mom_nowcast_early  — the FIRST nowcast in the stored path (earliest as-of)
  * cpi_mom_actual         — the realized print the nowcast is graded against
  * core equivalents (free, carried along)

Timing caveat for benchmarking: the final nowcast uses data up to ~release day (into month
M+1), i.e. ~2 weeks MORE information than our end-of-month-M forecast. So it is a
conservative (hard) bar, not a perfectly matched information set. Stored as its own
`cf_nowcast` table — NOT mixed into `observations`, which feeds feature building.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from sqlalchemy import Engine

from macro_nowcast.db.session import make_engine

NOWCAST_MONTH_URL = (
    "https://www.clevelandfed.org/-/media/files/webcharts/"
    "inflationnowcasting/nowcast_month.json?sc_lang=en"
)
TABLE = "cf_nowcast"


def fetch_raw(dest: Path) -> Path:
    """Download the monthly-nowcast JSON to `dest` (bypasses any stale env proxy). Returns dest."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(
        NOWCAST_MONTH_URL,
        headers={"User-Agent": "Mozilla/5.0"},
        proxies={"http": None, "https": None},  # ignore stale HTTP(S)_PROXY env vars
        timeout=60,
    )
    resp.raise_for_status()
    dest.write_bytes(resp.content)
    return dest


def _last(ds: dict) -> float | None:
    """Last non-empty float in a FusionCharts dataset's 'data' list (the final/most-informed value)."""
    vals = [p.get("value", "") for p in ds.get("data", [])]
    vals = [v for v in vals if v not in ("", None)]
    return float(vals[-1]) if vals else None


def _first(ds: dict) -> float | None:
    """First non-empty float in a dataset's 'data' list (the earliest stored as-of value)."""
    vals = [p.get("value", "") for p in ds.get("data", [])]
    vals = [v for v in vals if v not in ("", None)]
    return float(vals[0]) if vals else None


def parse(raw: list) -> pd.DataFrame:
    """Turn the raw chart list into one tidy row per reference month (sorted ascending)."""
    rows = []
    for chart in raw:
        sub = chart["chart"].get("subcaption")  # 'YYYY-M'
        try:
            year, month = (int(x) for x in sub.split("-"))
        except (AttributeError, ValueError):
            continue
        by_name = {ds.get("seriesname"): ds for ds in chart.get("dataset", [])}
        cpi = by_name.get("CPI Inflation", {})
        cats = chart.get("categories", [{}])[0].get("category", [])
        n_updates = len([p for p in cpi.get("data", []) if p.get("value") not in ("", None)])
        rows.append(
            {
                "ref_month": pd.Timestamp(year=year, month=month, day=1),
                "cpi_mom_nowcast": _last(cpi),
                "cpi_mom_nowcast_early": _first(cpi),
                "cpi_mom_actual": _last(by_name.get("Actual CPI Inflation", {})),
                "corecpi_mom_nowcast": _last(by_name.get("Core CPI Inflation", {})),
                "corecpi_mom_actual": _last(by_name.get("Actual Core CPI Inflation", {})),
                "asof_label": cats[-1].get("label") if cats else None,
                "n_updates": n_updates,
                "source": "CLEVELAND_FED",
            }
        )
    df = pd.DataFrame(rows).sort_values("ref_month").reset_index(drop=True)
    df["ingested_at"] = datetime.now(timezone.utc)
    return df


def store(df: pd.DataFrame, engine: Engine, table: str = TABLE) -> int:
    """Write the tidy nowcast frame to its own SQLite table (full replace). Returns row count."""
    df.to_sql(table, engine, if_exists="replace", index=False)
    return len(df)


def ingest(engine: Engine | None = None, cache: Path | None = None) -> pd.DataFrame:
    """Download → parse → store the Cleveland Fed monthly CPI nowcast. Returns the stored frame."""
    engine = engine or make_engine()
    from macro_nowcast import config

    cache = cache or (config.DB_PATH.parent / "raw" / "cleveland_fed_nowcast_month.json")
    fetch_raw(cache)
    raw = json.loads(cache.read_text(encoding="utf-8"))
    df = parse(raw)
    store(df, engine)
    return df


if __name__ == "__main__":
    frame = ingest()
    both = frame.dropna(subset=["cpi_mom_nowcast", "cpi_mom_actual"])
    print(f"Cleveland Fed CPI nowcast stored -> table '{TABLE}': {len(frame)} months "
          f"({frame['ref_month'].min():%Y-%m} .. {frame['ref_month'].max():%Y-%m}); "
          f"{len(both)} with nowcast AND actual.")
