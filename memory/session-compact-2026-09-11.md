## COMPACT — 2026-09-11 (covers since 2026-09-10)

**In one line:** Added the Cleveland Fed nowcast as a professional benchmark, built Stage 5 (the report), and settled the headline: our standalone model (RMSE 0.175, ~43% skill) plus a free-Fed-blend option (0.144). Pipeline is now end-to-end complete.

### WHAT CHANGED
- **Cleveland Fed nowcast ingested** → new `ingest/cleveland_fed.py` (parses the free JSON behind their chart; no key, no scraping) → tidy table `cf_nowcast` in `data/macro.db` (159 months 2013-07..2026-09, 155 with nowcast+actual). Raw cached to `data/raw/`. Verified: CF "actual" vs our first-print target corr 0.996.
- **Pre-release cutoff switch** added to `features/build.py` (`cutoff_mode="eom"|"pre_release"`). pre_release = day before the CPI print (trading/consensus-matched timing). Finding: cutoff alone barely changes accuracy (42.8%→42.5%) — our edge is energy, already complete at end-of-month.
- **Consensus benchmark done.** vs Cleveland Fed (matched timing, 153 mo): Fed 0.148 beats our 0.174 head-to-head; BUT the **simple 50/50 blend = 0.144 beats the Fed alone** (we add info; we hold up better in 2020/2021). Feeding Fed as a model *feature* → only ~0.167, dominated by the blend → rejected.
- **Stage 5 report built** → `report/build.py` (well-documented; computes everything fresh, 4 walk-forwards) + wired `macro-report`. Emits `reports/{date}_baseline.md` + clean pred-vs-actual PNG. Added `tests/test_report.py` (fast helper tests). **12/12 tests pass.**
- Surprise/trading reality check: timing-matched edge over consensus is thin (~54% correct side). Bryant clarified goal = a robust predictor + know how it compares to consensus, NOT live trading → CF benchmark is the right tool, no paid data needed.

### WHERE THINGS STAND
- **Pipeline COMPLETE, Stages 1–5.** Headline: standalone ensemble RMSE **0.175 / 42.8% skill / 80% dir / 69% hit**, 17/17 years beat naive, robustness 42.1%. Blend-with-Fed 0.144. Leak audit: drop energy → 42.8%→16.1% (edge is real). Report at `reports/2026-09-11_baseline.md`. 19 features.
- FMP key in `.env` but **free tier does NOT include the economic calendar** (real street consensus is paid) — parked; CF is the free professional benchmark we use instead.

### DO NEXT
1. Nothing required — baseline is done. Optional: swap target to core CPI/PCE (config switch) and re-run; or a proper alt-data effort if the surprise-edge angle is ever revived.
- Blocked on: nothing.

### DECISIONS LOCKED
- Headline = TWO numbers: standalone 0.175 (ours, self-contained) + blend 0.144 (with free Fed nowcast). Drop the Fed-as-feature 0.167 (dominated). — clean, honest story.
- Consensus benchmark = Cleveland Fed nowcast (free, professional, monthly). FMP free tier can't give street consensus; real consensus is paid, not needed for the stated goal.
- Report computes all numbers fresh from the DB (nothing hard-coded). — can't drift from code.

### ADDENDUM (later same day) — published to GitHub + live forecast built
- **Formal PDF report** `report/paper.py` (reportlab; no LaTeX on this box) → `docs/CPI_Nowcast_Baseline_Report.pdf` (3 pp). `macro-report` = markdown; paper module = PDF.
- **Pushed to GitHub: https://github.com/bryantt88/macro-cpi-nowcast (PUBLIC, account bryantt88).** `.env`/raw-cache gitignored + verified absent on remote. **Claude removed as contributor** (stripped `Co-Authored-By`/`Claude-Session` trailers from ALL commits via filter-branch; sole contributor = bryantt88). NOTE: keep future commits Claude-free (Bryant's standing request).
- **Live nowcast capability:** added `include_pending` to `features/build.py` (appends unreleased months, target=NaN, features still point-in-time) → new `report/forecast_note.py` (`macro`… `python -m macro_nowcast.report.forecast_note <consensus>`) → one-page dated PDF note.
- **AUGUST 2026 CPI forecast (print due ~2026-09-11/12):** our model **+0.46%**, blend **+0.41%**, Fed nowcast +0.36%, vs street consensus **+0.40%** (Bryant-provided), naive (July) +0.07%. 68% band +0.28..+0.63. **Read: firm, ABOVE-average month** (hist avg 0.21, recent 0.25) driven by energy (gasoline +3.2%, WTI +4.1%, DXY −1.4%); roughly in line w/ consensus, mild upside tilt, low conviction on surprise direction. → `docs/CPI_Forecast_Note_2026_08.pdf`. 12/12 tests.
