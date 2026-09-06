# Daily Log — Macro Indicator Predictor

## 2026-08-19
- Scaffolded the project's file management + workflow to match the Credit Rating and Factor-Alpha
  (Linear Regression) projects, before any modelling work.
- Created `.claude/commands/` with the four standard slash skills: `/compact` (cumulative-memory
  version, from the Factor-Alpha project), `/concise-answer`, `/pm-review` (retargeted to a macro
  strategist / multi-asset PM), `/short-code` (retargeted to this predictor's outputs).
- Created `.claude/settings.json` (empty permissions skeleton) + `.claude/settings.local.json`
  (empty allow-list; permissions will accumulate as approved — none pre-granted).
- Set up `memory/`: `MEMORY.md` (index only), `project-roadmap.md` (goal = TBD, kickoff open
  questions listed, status = SCAFFOLDED), and this `daily-log.md`.
- Added root `CLAUDE.md` operating-rules contract (house-style pointers, hard rules, memory pointers).
- **Not started yet:** the actual predictor. Goal, target indicator, horizon, data sources, method,
  and baseline are all still to be defined with Bryant at kickoff.
- **NEXT:** kickoff — answer the open questions in `project-roadmap.md`, then lock the build order.

## 2026-08-20
- **Spec locked** from Bryant's project note (Macro Economic Prediction Model). Target = headline CPI
  `CPIAUCSL`, MoM %, 1-month-ahead, config-swappable. ALFRED vintages (first-print, no look-ahead).
  Models LightGBM + ridge; expanding walk-forward only; metrics RMSE/MAE/directional/hit-vs-naive.
- Walked Bryant through the whole methodology in plain language (he knows markets, learning the tech):
  what the stack does, the 5 stages, point-in-time / no-look-ahead (closing-price-backtest analogy),
  walk-forward vs k-fold, and "beat naive".
- **Naive baseline clarified = persistence only** ("next MoM = this MoM"), NOT the 0%/level random walk.
  Bryant confirmed persistence only; do not add the 0% baseline.
- Discussed whether we can backtest professionally without overfitting → yes; documented the
  anti-overfitting protocol in the roadmap (few economic features, strong regularization, tune only
  in-window, pre-registered spec, report fold-by-fold + report failure). Edge source = real-time
  energy/market signal on the in-progress month that persistence is blind to → why headline is beatable.
- Causality insight (Bryant's): inflation drives OIS/rate-futures, not the reverse (12–18m lag the other
  way). So they're circular as CPI predictors → saved `reference-rates-endogeneity.md` (parked idea).
- Reviewed the full input list with per-item reasoning. Flagged weak-for-1-month features (gold, SPY,
  industrial production, Treasury fiscal, rates=circular) and stronger MISSING free ones: retail
  gasoline (`GASREGW`, weekly — biggest cheap win), PPI (pipeline), food commodities (~13% of CPI),
  Henry Hub gas; Zillow rent for trend (leads ~1yr, not next-month).
- **Ran `/compact`.** No code written yet — still scaffold only.
- **NEXT:** (1) Bryant decides whether to add gasoline/PPI/food + demote gold/SPY/fiscal; (2) then
  Stage 1 scaffold. Need a free FRED API key before Stage 2.

## 2026-09-07
- **Input set LOCKED.** Bryant approved the full 2026-08-20 proposal: ADD retail gasoline `GASREGW`
  (weekly), PPI, food commodities, Henry Hub nat-gas (all mechanically inside the CPI basket); DEMOTE
  gold/SPY/industrial-production/Treasury-fiscal/rates-block to optional context (kept in ingestion,
  down-weighted downstream — rates circular per [[reference-rates-endogeneity]]); Zillow rent stays Phase-2.
- **Answered Bryant's "is this many factors a burden?"** Framed sources-vs-features: adding sources is
  cheap; the burden is at feature engineering. ~300 monthly real-time obs (fewer in early folds) → curse
  of dimensionality if features approach obs count. Guardrail agreed: curate ~15–30 features (not an
  exhaustive transform cross-product); rely on ridge L2 + shallow LightGBM to shrink correlated inputs;
  a model that crushes naive = suspected leak. Recorded as a locked decision in the roadmap.
- Updated `project-roadmap.md`: source list, new locked decision, OPEN→RESOLVED, status line. No code yet.
- **NEXT:** build Stage 1 (scaffold — pyproject, src layout, `.env.example`, README). Get a free FRED API
  key before Stage 2.
- **Inflation LEVEL as feature (Bryant):** include CPI YoY (regime) alongside MoM; exclude raw index level
  (non-stationary). Recorded in roadmap Stage-3 defaults.
- **Clarified Stage 1 ≠ data extraction.** Stage 1 = scaffold (empty skeleton + DB schema); Stage 2 =
  ingestion (the actual data pull, needs FRED key).

## 2026-09-07 (cont.) — Stage 1 built
- **Built Stage 1 scaffold, full tidy pipeline, verified.** Package `macro_nowcast` (src layout).
  - `config.py`: paths, `TargetSpec` (CPIAUCSL / mom_pct / 1m, env-swappable), and the LOCKED `CATALOG`
    of 20 `Series` (roles target/primary/context) as data. `BacktestConfig` (persistence baseline).
  - `db/schema.py`: tidy long `observations` table (series_id, obs_date, value NULLable, release_date,
    vintage_date, frequency, fetched_at; unique on series+date+vintage) + `series_catalog`. SQLAlchemy 2.0.
  - `db/session.py`: `make_engine` / `init_db` (create tables + idempotent catalog seed).
  - `ingest/base.py` (fetch/validate/store interface) + `fred.py` + `market.py` stubs (raise NotImplemented,
    Stage 2). `features/build.py` (Stage 3 stub), `models/baseline.py` (persistence — LIVE),
    `models/train.py` (Stage 4 stub), `report/build.py` (Stage 5 stub).
  - `cli.py`: 5 entry points; `cmd_initdb` live, others print "not until Stage N". pyproject wires all 5.
  - `README.md` with ASCII mega-plan flow chart (Bryant asked for it); `.env.example` (FRED slot);
    `.gitignore` (secrets, *.db, reports).
  - Verified: py_compile clean; `macro-initdb` created `data/macro.db` (2 tables, seeded 20 series:
    1 target/13 primary/6 context, 0 observations); `pytest` 4/4 pass (schema seed, idempotency, baseline).
- Env note: Python 3.12, git present, **no uv** (README gives pip fallback); all runtime deps already installed.
- **NOT done:** `git init` (deferred — folder is OneDrive-synced; ask Bryant before creating a repo).
- **NEXT:** Bryant provides a free FRED API key → then Stage 2 (ingestion). Stop-after-stage review gate.
