"""Markdown report writer (Stage 5 stub).

Emits reports/{run_date}_baseline.md: coverage, feature list, params, fold-by-fold table,
summary vs naive, and a pred-vs-actual plot. Carries a one-line plain-language read so a
non-technical PM can act on it. Not implemented yet.
"""
from __future__ import annotations

from pathlib import Path


def write_report(results: dict, run_date: str) -> Path:
    """Render the run's results to a markdown file and return its path. (Stage 5)"""
    raise NotImplementedError("Reporting lands in Stage 5.")
