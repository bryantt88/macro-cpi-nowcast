"""Common ingestion interface. Every source implements the same fetch/validate/store contract.

Stage 1 defines the shape only — concrete pulls land in Stage 2. Keeping one interface
means the rest of the pipeline never cares whether a series came from FRED or yfinance.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class Record:
    """A single normalized observation, ready to store in the `observations` table."""

    series_id: str
    source: str
    obs_date: date
    value: float | None            # None = genuine gap, never fabricated
    release_date: date | None
    vintage_date: date | None
    frequency: str
    fetched_at: datetime


class BaseSource(ABC):
    """Contract shared by every data source module."""

    source_name: str

    @abstractmethod
    def fetch(self, series_id: str) -> list[Record]:
        """Pull raw observations for one series and normalize to `Record`s. (Stage 2)"""

    @abstractmethod
    def validate(self, records: list[Record]) -> list[Record]:
        """Check row counts, gaps, and dtypes; log issues; raise on hard failure. (Stage 2)"""
