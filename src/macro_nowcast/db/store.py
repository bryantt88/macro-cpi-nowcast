"""Idempotent bulk-insert of observations into the tidy long table.

Uses SQLite INSERT ... ON CONFLICT DO NOTHING on (series_id, obs_date, vintage_date), so
re-running ingestion never duplicates rows. Chunked to stay under SQLite's variable limit.
"""
from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import Engine
from sqlalchemy.dialects.sqlite import insert

from macro_nowcast.db.schema import Observation
from macro_nowcast.ingest.base import Record

_CHUNK = 500  # rows per INSERT (x8 cols) — safely under SQLite's parameter cap


def store_records(engine: Engine, records: Iterable[Record]) -> int:
    """Insert records, skipping any that already exist. Returns the number of new rows."""
    rows = [
        {
            "series_id": r.series_id,
            "source": r.source,
            "obs_date": r.obs_date,
            "value": r.value,
            "release_date": r.release_date,
            "vintage_date": r.vintage_date,
            "frequency": r.frequency,
            "fetched_at": r.fetched_at,
        }
        for r in records
    ]
    if not rows:
        return 0
    inserted = 0
    with engine.begin() as conn:
        for i in range(0, len(rows), _CHUNK):
            chunk = rows[i : i + _CHUNK]
            stmt = insert(Observation).values(chunk).on_conflict_do_nothing(
                index_elements=["series_id", "obs_date", "vintage_date"]
            )
            result = conn.execute(stmt)
            inserted += result.rowcount if result.rowcount and result.rowcount > 0 else 0
    return inserted
