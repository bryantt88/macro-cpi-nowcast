"""Market-price source via yfinance (Stage 2 stub).

Daily prices (WTI, DXY, SPY, gold) are the real-time edge: they update DURING the
in-progress month, carrying signal the persistence baseline is blind to. For these,
`release_date == obs_date` (a close is known the day it prints). Not implemented yet.
"""
from __future__ import annotations

from macro_nowcast.ingest.base import BaseSource, Record


class MarketSource(BaseSource):
    """Fetches daily market prices; release date == observation date."""

    source_name = "YFINANCE"

    def fetch(self, series_id: str) -> list[Record]:
        """Pull daily history for the mapped ticker. (Stage 2)"""
        raise NotImplementedError("Market ingestion lands in Stage 2.")

    def validate(self, records: list[Record]) -> list[Record]:
        """Validate row counts / gaps / dtypes. (Stage 2)"""
        raise NotImplementedError("Market validation lands in Stage 2.")
