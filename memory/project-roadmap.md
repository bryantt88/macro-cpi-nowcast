# Project Roadmap — Macro Economic Prediction Model

**Goal (one sentence):** predict the **1-month-ahead MoM % change in US headline CPI** from free macro
data, on a strict point-in-time basis, and honestly report whether it beats a naive last-value guess.

## The decision the tool must get right
- Forecast next month's CPI MoM print **before the BLS releases it** — an in-house inflation nowcast.
- Must **beat the naive baseline** ("next MoM = this MoM") on out-of-sample RMSE/MAE/directional
  accuracy. If it doesn't, the report says so plainly.

## Target & method spec (from Bryant's project note, 2026-08-19)
- **Target:** headline all-items CPI = FRED `CPIAUCSL`; predict its MoM % change, 1 month ahead.
  Wired as a **config switch** so core CPI / other series swap in later ("swappable").
- **Data sources** (each its own module, same interface fetch/validate/store) — **input set LOCKED 2026-09-07**:
  (1) FRED — CPI, PCE, NFP, unemployment, ISM PMIs, retail sales, industrial production, fed funds,
  2y & 10y yields, **+ retail gasoline `GASREGW` (weekly), PPI, food commodities, Henry Hub nat-gas**;
  (2) US Treasury fiscal data API; (3) yfinance — SPY, DXY, WTI, gold. Rates block + gold/SPY/IP/fiscal
  are DEMOTED to optional context (kept in ingestion, down-weighted at feature/model stage), not dropped.
- **Models:** LightGBM + ridge baseline. **Validation:** expanding-window walk-forward ONLY (no k-fold).
- **Metrics:** OOS RMSE, MAE, directional accuracy, hit-rate vs naive last-value.
- **Stack:** Python 3.11+, uv, pandas, numpy, scikit-learn, lightgbm, SQLite via SQLAlchemy, requests,
  pytest, ruff.

## Build order & status (STRICT — stop after each stage)
1. [x] **Scaffold** — DONE 2026-09-07. pyproject (src layout, `macro_nowcast` pkg, 5 CLI entry points),
   `.env.example` (FRED key slot), `.gitignore`, README (with mega-plan flow chart). Tidy long DB schema
   (`observations` + `series_catalog`) via SQLAlchemy 2.0; `init_db` creates + seeds 20 series (1 target /
   13 primary / 6 context). Persistence baseline implemented. 4/4 tests pass; `macro-initdb` verified.
   NOT yet done: `git init` (deferred — ask Bryant; OneDrive-synced folder).
2. [ ] **Ingestion** — one module per source → SQLite schema (series_id, date, value, source,
   release_date, fetched_at). Retry w/ backoff, log row counts + gaps, mock HTTP in tests.
3. [ ] **Features** — strict point-in-time (stamped at RELEASE date, never reference date). Defaults:
   MoM, YoY, PMI diffusion, 10y−2y slope, real-fed-funds proxy, 12/24m rolling z-scores, lagged target.
   **Inflation LEVEL/regime as a feature (Bryant, 2026-09-07):** include CPI YoY (the inflation "level" —
   captures 2%-world vs 7%-world regime) AND MoM. Do NOT feed the raw CPI index level (non-stationary →
   spurious fits/leakage); YoY is the stationary way to express "level." Already implied by YoY default;
   noted explicitly so it isn't dropped.
4. [ ] **Model + validation** — LightGBM + ridge; expanding walk-forward; metrics above; state plainly
   if it doesn't beat naive.
5. [ ] **Report** — markdown (coverage, features, params, fold-by-fold, summary, pred-vs-actual plot) →
   `reports/{run_date}_baseline.md`.

## Decisions locked (do not revisit without reason)
- **Target = headline CPI `CPIAUCSL`, MoM % change, 1-month-ahead** (2026-08-19). Config-swappable.
- **Point-in-time = ALFRED vintages** (2026-08-19) — use FRED's vintage archive so each value is the
  FIRST print as actually published; revisions cannot leak backward. Strict no-look-ahead. Chosen over
  the simpler "latest values + release-date lag" because the whole point is a defensible backtest.
- **Naive baseline = persistence ONLY** ("next MoM = this MoM"), i.e. carry forward the last MoM print
  (NOT the 0%/level-walk). Confirmed 2026-08-19 — do not add the 0% baseline. Must be beaten OOS or
  reported as not beaten.
- **Source of expected edge = real-time energy/market signal on the in-progress month** (WTI/gasoline,
  DXY, ISM prices-paid) that persistence is blind to. This is why headline (energy-heavy) is beatable
  and is the reason to start there vs stickier core. Grounded, not data-mined.
- **Anti-overfitting protocol (locked 2026-08-19):** few economically-motivated features (not mined);
  strong regularization (ridge; shallow LightGBM — low depth/few leaves/high min-samples); tune
  hyperparameters ONLY within each training window (never on test scores); pre-registered spec (no
  config changes chasing OOS results); report fold-by-fold + report failure honestly. "Good" = modest,
  stable edge (better RMSE + >50% direction) consistent across folds — a model that crushes naive is a
  suspected leak, not a win.
- **Input set LOCKED (2026-09-07).** Bryant approved adding all four proposed FRED series (retail gasoline
  `GASREGW`, PPI, food commodities, Henry Hub gas) — all mechanically inside the CPI basket. Gold, SPY,
  industrial production, Treasury fiscal, and the rates block are DEMOTED (kept in ingestion as optional
  context, down-weighted at feature/model stage per the endogeneity note), NOT removed. Zillow rent stays
  Phase-2 (longer-horizon). **Feature-count discipline (agreed):** adding sources is cheap; the burden is
  at feature engineering. ~300 monthly real-time obs (fewer in early folds) → keep the curated feature set
  ~15–30, NOT an exhaustive transform cross-product. Lean on ridge L2 + shallow LightGBM to shrink the many
  correlated inputs. A model that crushes naive = suspected leak, not a win.
- **Walk-forward only, expanding window. No k-fold.** No look-ahead. No silent failures (log, retry, raise).
- **No magic numbers / no hardcoded paths.** All config in `config.py` or `.env`. Type hints + one-line
  docstring on every public function. Tests for every data + feature module.
- **File/system convention (2026-08-19):** mirrors the Credit Rating / Factor-Alpha setup — in-repo
  `memory/` is canonical, `.claude/commands/` holds the four slash skills, `/compact` maintains both the
  in-repo memory and the auto-loaded store.

## RESOLVED DECISION (2026-09-07) — input set locked
Reviewed the input list 2026-08-19/20; **Bryant approved the full proposal 2026-09-07.** Outcome:
- **ADDED (free via FRED, mechanically linked to CPI):** retail gasoline `GASREGW` (weekly; biggest cheap
  win — actual pump price in CPI energy basket), PPI (pipeline costs lead CPI), food commodities (~13% of
  CPI, was absent), Henry Hub natural gas.
- **DEMOTED to optional context (kept in ingestion, down-weighted downstream):** gold, SPY, industrial
  production, Treasury fiscal data, and the rates block (fed funds/2y/10y — circular per
  [[reference-rates-endogeneity]]).
- **Phase-2 / longer-horizon:** Zillow rent index — shelter ≈ ⅓ of CPI, leads CPI-shelter ~1yr; trend not
  next-month print.
- **Feature-count guardrail agreed:** sources cheap, features are the burden → curate ~15–30 features
  (not a transform cross-product); ridge + shallow LightGBM to absorb the many correlated inputs.

## Needed from Bryant
- **Free FRED API key** (fred.stlouisfed.org) — required to run Stage 2. Goes in a local gitignored
  `.env`; Stage 1 only creates the `.env.example` slot. Never committed.

## Status: STAGE 1 (SCAFFOLD) DONE (2026-09-07). Spec + input set locked. Code builds + tests pass.
Next: **Stage 2 (ingestion)** — implement `ingest/fred.py` (ALFRED vintages) + `ingest/market.py`
(yfinance), pull the 20 catalog series into the tidy store. **BLOCKER: need a free FRED API key** in a
local `.env` first. Stages run strictly in order, stopping after each for review.
