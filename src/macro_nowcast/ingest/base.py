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
    def fetch(self, series_id: str, frequency: str, point_in_time: bool = False) -> list[Record]:
        """Pull raw observations for one series and normalize to `Record`s.

        point_in_time=True -> return first-print vintages (revised macro series);
        False -> full history as-published (never-revised prices/rates/surveys).
        """

    def validate(self, series_id: str, records: list[Record]) -> list[Record]:
        """Fail on an empty pull; otherwise pass records through (gaps kept as NULL values)."""
        if not records:
            raise ValueError(f"{series_id}: source returned zero observations.")
        return records
