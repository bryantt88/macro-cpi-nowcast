"""Storage layer: inserts land, gaps stay NULL, and re-inserting the same rows is a no-op."""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from sqlalchemy import func, select

from macro_nowcast.db.schema import Observation
from macro_nowcast.db.session import init_db, make_engine, make_session_factory
from macro_nowcast.db.store import store_records
from macro_nowcast.ingest.base import Record


def _rec(obs_date: date, value: float | None) -> Record:
    """Build one CPIAUCSL Record for testing."""
    return Record("CPIAUCSL", "FRED", obs_date, value, obs_date, obs_date, "M", datetime(2026, 9, 7))


def test_store_inserts_and_is_idempotent(tmp_path: Path) -> None:
    """First store inserts all rows; storing the same rows again inserts nothing new."""
    engine = make_engine(tmp_path / "s.db")
    init_db(engine)
    recs = [_rec(date(2026, 1, 1), 0.3), _rec(date(2026, 2, 1), None)]  # one real, one gap

    assert store_records(engine, recs) == 2
    assert store_records(engine, recs) == 0  # ON CONFLICT DO NOTHING

    with make_session_factory(engine)() as session:
        assert session.scalar(select(func.count()).select_from(Observation)) == 2
        gap = session.scalar(select(Observation).where(Observation.obs_date == date(2026, 2, 1)))
        assert gap.value is None  # genuine gap preserved as NULL, never fabricated
