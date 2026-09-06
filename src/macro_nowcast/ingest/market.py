"""Market-price source via yfinance (WTI, DXY, SPY, gold).

Daily prices are the real-time edge: known the day they print, so release_date == obs_date
and there is nothing to revise. Full available history is pulled (archive-start irrelevant).
"""
from __future__ import annotations

from datetime import datetime

import yfinance as yf

from macro_nowcast import config
from macro_nowcast.ingest.base import BaseSource, Record


class MarketSource(BaseSource):
    """Fetches daily market closes; release date == observation date."""

    source_name = "YFINANCE"

    def fetch(self, series_id: str, frequency: str, point_in_time: bool = False) -> list[Record]:
        """Return full daily close history for the mapped ticker as normalized Records."""
        ticker = config.YF_TICKERS[series_id]
        df = yf.Ticker(ticker).history(period="max", interval="1d", auto_adjust=False)
        fetched_at = datetime.utcnow()
        records: list[Record] = []
        if df.empty or "Close" not in df:
            return records
        for ts, close in df["Close"].dropna().items():
            obs_date = ts.date()
            records.append(
                Record(
                    series_id=series_id,
                    source=self.source_name,
                    obs_date=obs_date,
                    value=float(close),
                    release_date=obs_date,   # a close is known the day it prints
                    vintage_date=obs_date,
                    frequency=frequency,
                    fetched_at=fetched_at,
                )
            )
        return records
