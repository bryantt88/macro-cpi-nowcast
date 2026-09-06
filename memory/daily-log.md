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

## 2026-09-07 (cont.) — FRED key + Stage 2 ingestion DONE
- Bryant added the FRED key (had pasted it into `.env.example` = git-tracked; moved it to `.env`
  gitignored, blanked the template). Verified: FRED `/series/observations` 200 + ALFRED vintage query 200.
- **git init done (option 2, local only)** — repo-local identity set, first commit `31f43a6` (Stage 1
  scaffold). `.env` + `data/*.db` correctly gitignored. No remote/GitHub.
- **Decided data horizons from real FRED availability** (queried, not guessed). Two dates per series:
  obs_start (value exists) vs 1st_vintage (point-in-time exists). Plan: ingest FULL history per series;
  MODEL on ~2000→present (~310 monthly). Key trick: PRICES are never revised → use full history
  as-published; only genuinely-revised macro series need first-print vintages.
- **Built + ran Stage 2.** `ingest/fred.py` (first-print via ALFRED output_type=4 for revised series;
  full as-published history otherwise — gated by new `Series.point_in_time` flag), `ingest/market.py`
  (yfinance daily closes, release=obs date), `db/store.py` (chunked idempotent upsert). CLI dispatcher
  added (`python -m macro_nowcast.cli <cmd>`). Gotcha fixed: output_type=4 needs an explicit realtime
  span (1776-07-04..9999-12-31) or FRED 400s ("no vintage dates for today").
- **Result: 21 series, 83,145 rows, 0 failures, DB ~14 MB.** Earliest: INDPRO 1927; target CPIAUCSL
  first-print 1972; newest PPIFIS 2014-02. Gaps preserved as NULL (never fabricated). 5/5 tests pass.
- NAPM (ISM PMI) discontinued on FRED → replaced by Philly Fed (1968) + NY Fed (2001) prices-paid.
- **NEXT:** Stage 3 (point-in-time features). Stop-after-stage review gate.

## 2026-09-07 (cont.) — Stage 3 features DONE
- Clarified with Bryant: pre-2000 data is NOT trained/scored on, but IS used as look-back to compute the
  earliest in-window features (YoY, 24m z-scores, lags). 2000 = earliest date the full core feature set
  exists point-in-time. Locked `min_train_months=120` (primary; 2007-start robustness run secondary).
  Explained WTI (daily CL=F, real-time edge) vs WTISPLC (monthly avg, long history) — complementary.
- **Built Stage 3.** `features/build.py`: monthly grid from CPI first-print; forecast cutoff = END of
  month M. `asof_known` = merge_asof on release_date = the no-look-ahead join. 18 curated features (see
  roadmap). Written to SQLite `features` table via cmd_features (319 rows, 2000-01..2026-07, 317 trainable).
- **Timing BUG caught by a sanity check + fixed:** first passed month-START grid as the cutoff → features
  lagged an extra month (cpi_mom_lag1==target(M-2)) AND inconsistent with month-M market data. Fixed to
  month-END cutoffs (grid + MonthEnd(0)). Re-verified: `cpi_mom_lag1(M)==target(M-1)` = 100% (persistence
  correct), lag ladder shifts by exactly 1. Lesson: always cross-check the persistence identity after
  building features.
- Added `config.MODEL_START=2000-01-01`. Missingness sane: ppifis ~54% (optional recent), retail 6%,
  ny_pricespaid 6%, wti 2.5%, rest ~0. 7/7 tests (incl. no-look-ahead invariant test_features.py).
- **NEXT:** Stage 4 (model + expanding walk-forward vs persistence). Stop-after-stage review gate.

## 2026-09-07 (cont.) — Stage 4 model + walk-forward DONE (headline result)
- Built `models/train.py`: ridge (Pipeline: median impute + StandardScaler + RidgeCV in-window) + shallow
  regularized LightGBM (NaN-native) + mean ensemble; expanding walk-forward, retrain every month.
  `cmd_train` runs PRIMARY (min_train=120) + ROBUSTNESS (min_train=84, 2007-start) and stores OOS preds.
- **RESULT: ensemble beats persistence ~40% RMSE, consistently.** Primary (196 mo, 2010-2026): ens RMSE
  0.184 vs naive 0.305 = 39.6% skill, 66% hit, 78% dir-acc. Robustness through 2008 crash (232 mo): 39.8%
  skill, 68% hit. Ridge and LGBM individually ~34-36% skill; ensemble best.
- **Applied our own 'crushing naive = suspected leak' rule → ran leak audit.** Dropping energy features
  (wti/gasoline/natgas) cuts skill 39.6%->15.4%: ~60% of edge = the pre-registered real-time energy signal
  (legit — daily prices known before CPI release). Traces cleanly to economic thesis → NOT a leak. This is
  why we chose energy-heavy HEADLINE CPI. Defensible win.
- Two display bugs fixed: NaN persistence value (rare CPI first-print gap) poisoned non-nan-aware RMSE ->
  score all models on the same finite-target/persistence months; em-dash output tripped grep binary mode ->
  ASCII 'n/a'. 9/9 tests (added test_train.py: shapes + persistence skill==0 identity).
- **NEXT:** Stage 5 (markdown report + pred-vs-actual plot, include ablation as leak evidence). Review gate.
