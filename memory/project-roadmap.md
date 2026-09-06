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
2. [x] **Ingestion** — DONE 2026-09-07. `ingest/fred.py` + `ingest/market.py` + `db/store.py` (idempotent
   ON CONFLICT DO NOTHING). Pulled all 21 series, 83,145 rows, 0 failures, DB ~14 MB. FRED revised series
   (point_in_time=True: CPI/PPIACO/PPIFIS/PCEPI/PAYEMS/UNRATE/RSAFS/INDPRO) via ALFRED output_type=4
   FIRST-PRINT across full realtime span (release_date = true publish date). Never-revised prices/rates/
   surveys + all yfinance = full history as-published (release_date = obs_date). NAPM (ISM PMI) was
   discontinued on FRED → replaced with Philly Fed (PPCDFSA066MSFRBPHI, from 1968) + NY Fed
   (PPCDISA066MSFRBNY, from 2001) prices-paid diffusion. Earliest overall: INDPRO 1927; target CPIAUCSL
   first-print from 1972. Newest-starting: PPIFIS 2014-02. 5/5 tests pass.
3. [x] **Features** — DONE 2026-09-07. `features/build.py` → 319 monthly rows (2000-01..2026-07), 317
   trainable, **18 curated features** written to a `features` table in the SQLite DB. Forecast cutoff =
   END of month M: month-M market aggregates are in; CPI(M-1)/PPI(M-1) etc. are released; CPI(M) is the
   label. No-look-ahead enforced by `asof_known` (merge_asof on release_date) — unit-tested + a live
   invariant confirms `cpi_mom_lag1(M) == target(M-1)` (persistence) at 100%. Features: cpi_mom_lag1/2/3,
   cpi_yoy_lag1 (inflation LEVEL/regime — raw index level deliberately excluded), cpi_mom_z24, wti_mom,
   gasoline_mom, natgas_mom, dxy_mom, slope_10y2y, ppi_mom_lag1, payems_mom_lag1, retail_mom_lag1,
   ppifis_mom_lag1 (optional, ~54% NaN pre-2014), unrate_lag1, phil_pricespaid, ny_pricespaid,
   food_mom_lag1 (lagged 1mo — publishes into M+1). 7/7 tests pass.
4. [x] **Model + validation** — DONE 2026-09-07. `models/train.py` `walk_forward_eval`: ridge (median-
   impute + standardize + in-window RidgeCV alpha) + shallow regularized LightGBM (num_leaves=7, depth=3,
   min_child=25, subsample/colsample 0.8, reg_lambda=1, lr=0.03, 300 trees) + mean ensemble. Expanding
   walk-forward, retrain each month. **RESULT: ensemble beats persistence by ~40% RMSE** — PRIMARY
   (min_train=120, 196 OOS mo 2010-2026): ens RMSE 0.184 vs naive 0.305, skill 39.6%, hit 66%, dir 78%.
   ROBUSTNESS (2007-start, 232 mo incl. 2008 oil crash): skill 39.8%, hit 68%. **Leak audit PASSED:**
   dropping energy features (WTI/gasoline/natgas) collapses skill 39.6%->15.4%, i.e. ~60% of edge = the
   pre-registered real-time energy signal (legit: daily prices known before CPI release). Not a leak.
   OOS predictions stored -> `oos_predictions` table. 9/9 tests.
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
- **Backtest window LOCKED (2026-09-07):** expanding walk-forward, `min_train_months = 120` (10yr).
  Training data begins ~2000; first ~10yr builds the initial window (not scored); **OOS backtest ≈ 2011→
  present (~180 one-month-ahead forecasts)**, each scored vs persistence. Chosen over a shorter min-train
  (84mo/2007-start) because macro monthly data is small and a fair, well-trained model per fold matters
  more than extra OOS months. **Secondary robustness run at Stage 4:** also report a 2007-start
  (min_train~84) pass so the thesis is tested through the 2008 oil crash. Primary verdict = the 120 run.
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

## Status: STAGE 4 (MODEL) DONE (2026-09-07). Ensemble beats persistence ~40% RMSE, robust + leak-audited.
Stages 1-4 complete; 9/9 tests. Next: **Stage 5 (report)** — markdown to `reports/{run_date}_baseline.md`:
coverage, feature list, params, fold-by-fold (or per-year) table, summary vs naive, pred-vs-actual plot,
+ a one-line plain-language read for a non-technical PM. Include the energy-ablation as the leak-audit
evidence. Then the pipeline is end-to-end complete for a first defensible baseline.
