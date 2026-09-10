"""Thin command-line entry points, one per pipeline stage (see pyproject [project.scripts]).

Only `cmd_initdb` (Stage 1) is live; the rest announce which stage will implement them,
so the full pipeline is visible and wired end-to-end from day one.
"""
from __future__ import annotations

import os
import sys

from macro_nowcast import config
from macro_nowcast.db.session import init_db, make_engine
from macro_nowcast.db.store import store_records
from macro_nowcast.ingest.fred import FredSource
from macro_nowcast.ingest.market import MarketSource


def cmd_initdb(argv: list[str] | None = None) -> int:
    """Stage 1: create the empty SQLite schema and seed the series catalog."""
    engine = make_engine()
    init_db(engine)
    print(f"Initialized database at: {config.DB_PATH}")
    print(f"Seeded {len(config.CATALOG)} series into series_catalog "
          f"(target = {config.TARGET.series_id}, horizon = {config.TARGET.horizon_months}m).")
    return 0


def _pending(stage: str) -> int:
    """Print a clear 'not yet' message for a stage that isn't built."""
    print(f"[{stage}] not implemented yet — build stages run strictly in order.", file=sys.stderr)
    return 1


def cmd_ingest(argv: list[str] | None = None) -> int:
    """Stage 2: pull every catalog series into the store; log range + gaps per series."""
    key = config.fred_api_key()
    if not key:
        print("FRED_API_KEY missing — add it to .env (see .env.example).", file=sys.stderr)
        return 1

    # yfinance/requests must not inherit any sandbox proxy for outbound calls.
    for var in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
        os.environ.pop(var, None)

    engine = make_engine()
    init_db(engine)  # ensure schema + catalog exist
    sources = {"FRED": FredSource(key), "YFINANCE": MarketSource()}

    total, failures = 0, 0
    print(f"{'series':<22}{'source':<10}{'rows':>7}{'new':>8}  {'range':<25}{'gaps':>6}")
    print("-" * 82)
    for s in config.CATALOG:
        src = sources[s.source]
        try:
            fetched = src.fetch(s.series_id, s.frequency, s.point_in_time)
            records = src.validate(s.series_id, fetched)
            new = store_records(engine, records)
            present = [r.obs_date for r in records if r.value is not None]
            gaps = len(records) - len(present)
            rng = f"{min(present)} .. {max(present)}" if present else "(no values)"
            print(f"{s.series_id:<22}{s.source:<10}{len(records):>7}{new:>8}  {rng:<25}{gaps:>6}")
            total += new
        except Exception as exc:  # log + continue; one bad series shouldn't sink the run
            failures += 1
            print(f"{s.series_id:<22}{s.source:<10}  ERROR: {exc}", file=sys.stderr)
    print("-" * 82)
    print(f"Stored {total} new rows across {len(config.CATALOG)} series ({failures} failed).")
    return 1 if failures else 0


def cmd_features(argv: list[str] | None = None) -> int:
    """Stage 3: build the point-in-time feature matrix and store it in the DB."""
    from macro_nowcast.features.build import build_features

    engine = make_engine()
    feats = build_features(engine)
    trainable = feats["target"].notna()
    feats.reset_index(names="ref_month").to_sql("features", engine, if_exists="replace", index=False)

    cols = [c for c in feats.columns if c != "target"]
    print(f"Built features table: {feats.shape[0]} rows x {len(cols)} features "
          f"(+ target). Range: {feats.index.min().date()} .. {feats.index.max().date()}.")
    print(f"Rows with a known target (trainable): {int(trainable.sum())}")
    print("Missing % per feature (blank = optional/recent, filled downstream):")
    miss = (feats[cols].isna().mean() * 100).round(1).sort_values(ascending=False)
    for name, pct in miss.items():
        print(f"  {name:<18} {pct:>5.1f}%")
    return 0


def _print_metrics(title: str, res: dict) -> None:
    """Print a per-model metrics table + honest verdict for one walk-forward run."""
    m = res["metrics"]
    print(f"\n{title}: {res['n_oos']} OOS months, min_train={res['min_train']} "
          f"({res['oos'].index.min().date()} .. {res['oos'].index.max().date()})")
    print(f"  {'model':<12}{'RMSE':>8}{'MAE':>8}{'RMSEskill':>11}{'dir_acc':>9}{'hit_vs_naive':>14}")
    for name in ("persistence", "ridge", "lgbm", "ensemble"):
        r = m[name]
        skill = "n/a" if name == "persistence" else f"{r['rmse_skill']*100:.1f}%"
        dacc = "n/a" if name == "persistence" else f"{r['dir_acc']*100:.1f}%"
        hit = "n/a" if name == "persistence" else f"{r['hit_rate']*100:.1f}%"
        print(f"  {name:<12}{r['rmse']:>8.3f}{r['mae']:>8.3f}{skill:>11}{dacc:>9}{hit:>14}")
    best = min(("ridge", "lgbm", "ensemble"), key=lambda k: m[k]["rmse"])
    if m[best]["rmse"] < m["persistence"]["rmse"]:
        print(f"  VERDICT: '{best}' beats persistence by "
              f"{m[best]['rmse_skill']*100:.1f}% RMSE (hit {m[best]['hit_rate']*100:.0f}%).")
    else:
        print("  VERDICT: does NOT beat persistence out-of-sample — naive baseline wins.")


def cmd_train(argv: list[str] | None = None) -> int:
    """Stage 4: run walk-forward (primary min_train=120 + 2007-start robustness); score vs naive."""
    import pandas as pd

    from macro_nowcast.models.train import walk_forward_eval

    engine = make_engine()
    feats = pd.read_sql("SELECT * FROM features", engine, parse_dates=["ref_month"]).set_index("ref_month")

    primary = walk_forward_eval(feats, min_train=config.BACKTEST.min_train_months)
    _print_metrics("PRIMARY", primary)
    secondary = walk_forward_eval(feats, min_train=84)  # ~2007 start, spans the 2008 oil crash
    _print_metrics("ROBUSTNESS (2007-start)", secondary)

    primary["oos"].reset_index().to_sql("oos_predictions", engine, if_exists="replace", index=False)
    print("\nStored primary OOS predictions -> table 'oos_predictions'.")
    return 0


def cmd_report(argv: list[str] | None = None) -> int:
    """Stage 5: compute results fresh and write reports/{run_date}_baseline.md (+ chart)."""
    from macro_nowcast.report.build import write_report

    engine = make_engine()
    path = write_report(engine)
    print(f"Report written: {path}")
    print(f"Chart written:  {path.with_name(path.stem.replace('_baseline', '_pred_vs_actual') + '.png')}")
    return 0


_COMMANDS = {
    "initdb": cmd_initdb,
    "ingest": cmd_ingest,
    "features": cmd_features,
    "train": cmd_train,
    "report": cmd_report,
}


def main(argv: list[str] | None = None) -> int:
    """Dispatch `python -m macro_nowcast.cli <command>` (default: initdb)."""
    args = sys.argv[1:] if argv is None else argv
    cmd = args[0] if args else "initdb"
    if cmd not in _COMMANDS:
        print(f"unknown command '{cmd}'. choose from: {', '.join(_COMMANDS)}", file=sys.stderr)
        return 2
    return _COMMANDS[cmd](args[1:])


if __name__ == "__main__":
    raise SystemExit(main())
