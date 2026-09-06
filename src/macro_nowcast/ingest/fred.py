"""FRED / ALFRED source (Stage 2 stub).

Will pull first-print vintages via the ALFRED archive so each value is what was actually
published as of its release date (no revisions leaking backward). Not implemented yet.
"""
from __future__ import annotations

from macro_nowcast.ingest.base import BaseSource, Record


class FredSource(BaseSource):
    """Fetches FRED series with point-in-time (ALFRED) vintages."""

    source_name = "FRED"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def fetch(self, series_id: str) -> list[Record]:
        """Pull ALFRED vintages for `series_id`. (Stage 2)"""
        raise NotImplementedError("FRED ingestion lands in Stage 2.")

    def validate(self, records: list[Record]) -> list[Record]:
        """Validate row counts / gaps / dtypes. (Stage 2)"""
        raise NotImplementedError("FRED validation lands in Stage 2.")
