"""Stage 1 smoke tests: the schema builds and the catalog seeds correctly, in a temp DB."""
from __future__ import annotations

from pathlib import Path

from sqlalchemy import func, select

from macro_nowcast import config
from macro_nowcast.db.schema import Observation, SeriesCatalog
from macro_nowcast.db.session import init_db, make_engine, make_session_factory


def test_init_db_creates_tables_and_seeds_catalog(tmp_path: Path) -> None:
    """init_db builds both tables and seeds one catalog row per configured series."""
    engine = make_engine(tmp_path / "test.db")
    init_db(engine)

    with make_session_factory(engine)() as session:
        n_catalog = session.scalar(select(func.count()).select_from(SeriesCatalog))
        n_obs = session.scalar(select(func.count()).select_from(Observation))
        assert n_catalog == len(config.CATALOG)   # every configured series is registered
        assert n_obs == 0                          # Stage 1 stores no observations yet


def test_seed_is_idempotent(tmp_path: Path) -> None:
    """Running init_db twice does not duplicate catalog rows."""
    engine = make_engine(tmp_path / "test.db")
    init_db(engine)
    init_db(engine)

    with make_session_factory(engine)() as session:
        n_catalog = session.scalar(select(func.count()).select_from(SeriesCatalog))
        assert n_catalog == len(config.CATALOG)


def test_target_is_in_catalog() -> None:
    """The configured target series must exist in the catalog it seeds from."""
    ids = {s.series_id for s in config.CATALOG}
    assert config.TARGET.series_id in ids
