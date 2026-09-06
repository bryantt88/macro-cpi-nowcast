"""FRED / ALFRED source — pulls FIRST-PRINT (point-in-time) observations.

Uses the ALFRED `output_type=4` ("initial release only") endpoint so each stored value is
the number as first published, with `realtime_start` as its release date. Revisions cannot
leak backward. For never-revised price series this simply returns the value as-published.
"""
from __future__ import annotations

import time
from datetime import date, datetime

import requests

from macro_nowcast.ingest.base import BaseSource, Record

_BASE = "https://api.stlouisfed.org/fred/series/observations"
_MISSING = {".", "", None}


class FredSource(BaseSource):
    """Fetches FRED series with point-in-time (ALFRED first-release) values."""

    source_name = "FRED"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.session = requests.Session()
        self.session.trust_env = False  # don't inherit sandbox proxies

    def _get(self, params: dict, retries: int = 4) -> requests.Response:
        """GET with exponential backoff on transient errors; raise on final failure."""
        for attempt in range(retries):
            try:
                r = self.session.get(_BASE, params=params, timeout=60)
            except requests.RequestException:
                if attempt == retries - 1:
                    raise
                time.sleep(2**attempt)
                continue
            if r.status_code == 200:
                return r
            if r.status_code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(2**attempt)
                continue
            r.raise_for_status()
        raise RuntimeError("unreachable")

    def fetch(self, series_id: str, frequency: str, point_in_time: bool = False) -> list[Record]:
        """Return observations for `series_id` as normalized Records.

        Revised series (point_in_time=True): first-print via output_type=4 across the full
        real-time span, so release_date is the true publication date. Never-revised series:
        plain latest history, release_date == obs_date (nothing to revise).
        """
        params: dict[str, object] = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
        }
        if point_in_time:
            params.update(
                output_type=4,               # initial release only
                realtime_start="1776-07-04",  # FRED epoch -> whole vintage history
                realtime_end="9999-12-31",
            )
        observations = self._get(params).json().get("observations", [])
        fetched_at = datetime.utcnow()
        records: list[Record] = []
        for o in observations:
            raw = o.get("value")
            value = None if raw in _MISSING else float(raw)
            obs_date = date.fromisoformat(o["date"])
            if point_in_time:
                rt = o.get("realtime_start")
                release = date.fromisoformat(rt) if rt else obs_date
            else:
                release = obs_date  # as-published: value known on its own date
            records.append(
                Record(
                    series_id=series_id,
                    source=self.source_name,
                    obs_date=obs_date,
                    value=value,
                    release_date=release,
                    vintage_date=release,  # never NULL -> keeps upsert idempotent
                    frequency=frequency,
                    fetched_at=fetched_at,
                )
            )
        return records
