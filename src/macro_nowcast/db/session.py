"""Engine + session factory, and helpers to create/seed the empty schema (Stage 1)."""
from __future__ import annotations

from pathlib import Path

from sqlalchemy import Engine, create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from macro_nowcast import config
from macro_nowcast.db.schema import Base, SeriesCatalog


def make_engine(db_path: Path | None = None) -> Engine:
    """Return a SQLite engine for `db_path` (defaults to config.DB_PATH); creates the folder."""
    path = db_path or config.DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{path}", future=True)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Return a bound Session factory for the given engine."""
    return sessionmaker(bind=engine, future=True)


def init_db(engine: Engine) -> None:
    """Create all tables if absent, then seed the series catalog from config (idempotent)."""
    Base.metadata.create_all(engine)
    _seed_catalog(engine)


def _seed_catalog(engine: Engine) -> None:
    """Insert any catalog rows from config that aren't already stored. Never duplicates."""
    factory = make_session_factory(engine)
    with factory() as session:
        existing = set(session.scalars(select(SeriesCatalog.series_id)).all())
        for s in config.CATALOG:
            if s.series_id not in existing:
                session.add(
                    SeriesCatalog(
                        series_id=s.series_id,
                        source=s.source,
                        description=s.description,
                        frequency=s.frequency,
                        role=s.role,
                    )
                )
        session.commit()
