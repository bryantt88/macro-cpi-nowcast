"""Thin command-line entry points, one per pipeline stage (see pyproject [project.scripts]).

Only `cmd_initdb` (Stage 1) is live; the rest announce which stage will implement them,
so the full pipeline is visible and wired end-to-end from day one.
"""
from __future__ import annotations

import sys

from macro_nowcast import config
from macro_nowcast.db.session import init_db, make_engine


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
    """Stage 2: pull all catalog sources into the store."""
    return _pending("Stage 2: ingest")


def cmd_features(argv: list[str] | None = None) -> int:
    """Stage 3: build the point-in-time feature matrix."""
    return _pending("Stage 3: features")


def cmd_train(argv: list[str] | None = None) -> int:
    """Stage 4: walk-forward train + score vs persistence."""
    return _pending("Stage 4: train")


def cmd_report(argv: list[str] | None = None) -> int:
    """Stage 5: write the markdown report."""
    return _pending("Stage 5: report")


if __name__ == "__main__":
    raise SystemExit(cmd_initdb())
