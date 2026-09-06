"""SQLite schema (SQLAlchemy 2.0) — one tidy 'long' observations table + a series catalog.

Design goal: every data point, whatever its source, is one row with the same shape.
The `release_date` / `vintage_date` columns are what enforce NO LOOK-AHEAD: a value may
only be used by the model on or after the date it was actually published.
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


class SeriesCatalog(Base):
    """One row per indicator we track — provenance and metadata, not values."""

    __tablename__ = "series_catalog"

    series_id: Mapped[str] = mapped_column(String, primary_key=True)
    source: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    frequency: Mapped[str] = mapped_column(String, nullable=False)  # D | W | M
    role: Mapped[str] = mapped_column(String, nullable=False)       # target|primary|context


class Observation(Base):
    """One (series, period, vintage) data point. The tidy long-format fact table.

    `value` is nullable on purpose: a genuine gap is stored as NULL, never fabricated.
    """

    __tablename__ = "observations"
    __table_args__ = (
        # Same series + same period can appear under different vintages (revisions);
        # a given vintage of a given period is unique.
        UniqueConstraint("series_id", "obs_date", "vintage_date", name="uq_obs_series_date_vintage"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    series_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    obs_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)   # period the value describes
    value: Mapped[float | None] = mapped_column(Float, nullable=True)          # NULL = genuine gap
    release_date: Mapped[date | None] = mapped_column(Date, nullable=True)     # when published (ALFRED)
    vintage_date: Mapped[date | None] = mapped_column(Date, nullable=True)     # which ALFRED vintage
    frequency: Mapped[str] = mapped_column(String, nullable=False)             # D | W | M
    fetched_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
