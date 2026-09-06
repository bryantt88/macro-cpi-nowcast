# CLAUDE.md — Operating Rules

Read this at the start of every session. It is the short, high-signal contract for building this project.

## What this project is

**Macro Indicator Predictor** — *scope TBD at kickoff.* A tool to predict / nowcast one or more macro
indicators for the fund's decision-making. The exact target indicator(s), forecast horizon, data
sources, method, and the baseline it must beat are defined in `memory/project-roadmap.md` (see the
"open questions to settle at kickoff" section). Do not assume the spec — confirm it with Bryant first.

## Hard rules (do not violate)

1. **No fabricated numbers, ever.** If a figure can't be pulled or computed, mark it `null` /
   `unverified` and surface that in the output. Never fill a gap with a plausible guess. (This is the
   top failure mode to avoid across all of Bryant's projects.)
2. **No look-ahead / no leakage.** Macro series get revised. Respect vintages / release dates — a
   backtest must only use data that was actually available as of the forecast date. Never train or
   evaluate on a revised series as if it were the real-time print.
3. **Always beat a stated baseline.** Every forecast is judged against an explicit naive benchmark
   (random walk, consensus/SPF, AR) chosen up front — not against nothing.
4. **Auditable over clever.** Prefer the version a human can trust and defend to a PM over the one
   that is cleverer but opaque. Every displayed number must trace to a source or a computation.
5. **Sourced inputs.** Every external data point has a named source (FRED series id, ticker, vendor).

## Conventions

- **Language / stack:** Python by default (`pandas`, `numpy`, `statsmodels`; data via FRED / `yfinance`
  or agreed vendor). Confirm any ML/econometric library choice at kickoff.
- **Config over hardcoding:** lookback windows, horizons, thresholds, series ids, benchmark — in a
  config, not scattered literals.
- **Modular repo**, not one giant script. Lock the layout when the build order is set.
- **Built to *read*:** every output carries a one-line plain-language read + an interval/flag, so a
  non-technical PM can act on it.
- **House style:** for any Excel deliverable follow `../Joywin_Excel_House_Style.md`; for any memo
  follow `../Joywin_Memo_House_Style.md`. Bryant wants clean, simple, professional, industry-standard
  output — no clutter, no oversized chart markers.

## When in doubt

Prefer the version that is auditable and reproducible over the one that is clever. Ask before assuming
the project scope; the goal is a forecast a human can trust and defend.

## Project memory (read at session start)

Persistent context lives in `memory/` in this repo — read it first each session:
- `memory/project-roadmap.md` — goal, build order + status, decisions locked, next actions.
- `memory/daily-log.md` — dated session log; the most recent entry is where we left off.
- `memory/session-compact-<date>.md` — per-session handoffs written by `/compact`.

Custom commands live in `.claude/commands/`: `/compact` (session handoff + cumulative memory →
`memory/`), `/concise-answer`, `/pm-review` (macro-PM review of *this* predictor), `/short-code`.
Claude Code also keeps an auto-loaded memory index outside the repo that mirrors these facts.
