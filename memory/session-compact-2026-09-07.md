## COMPACT — 2026-09-07 (covers since 2026-08-20)

**In one line:** Built the full CPI-nowcast pipeline end-to-end (Stages 1–4); the ensemble beats persistence ~40% RMSE, leak-audited and robust through 2008/2020/2022.

### WHAT CHANGED
- Input set LOCKED — added gasoline/PPI/food/natgas; demoted gold/SPY/IndPro/fiscal/rates. ISM PMI dead on FRED → Philly + NY Fed prices-paid diffusion.
- Stage 1 scaffold — `macro_nowcast` src package, tidy SQLite long schema, 5 CLI commands. `git init` (local only), first commit.
- Stage 2 ingestion — 21 series, 83,145 rows. Revised series = ALFRED first-print (output_type=4 + full realtime span); never-revised prices = full history as-published (via `Series.point_in_time` flag). Earliest INDPRO 1927; CPI first-print 1972; PPIFIS 2014.
- Stage 3 features — 319×18 point-in-time matrix → `features` table. Forecast cutoff = END of month M. `asof_known` = merge_asof on release_date. Persistence identity `cpi_mom_lag1(M)==target(M-1)` verified 100%.
- Stage 4 model — ridge + shallow LightGBM + mean ensemble, expanding walk-forward. Ensemble RMSE 0.184 vs naive 0.305 = 39.6% skill, 66% hit, 78% dir, R²=0.60. Robust: 16/17 yrs (19/20 from 2007).
- Leak audit — drop energy features → skill 39.6%→15.4%; edge traces to pre-registered real-time energy. Not a leak.

### WHERE THINGS STAND
- Pipeline complete Stages 1–4. 9/9 tests pass. `data/macro.db` holds observations / series_catalog / features / oos_predictions. FRED key in `.env` (gitignored).

### DO NEXT
1. Build **Stage 5 (report)** → `reports/{run_date}_baseline.md`: coverage, feature list, params, per-year table, pred-vs-actual plot, energy-ablation as leak evidence, one-line PM read. Bake in grounding: signal std 0.29pp, R²=0.60, single-month caveat.
- Blocked on: nothing.

### DECISIONS LOCKED
- min_train=120 primary; 2007-start (84) robustness secondary.
- Naive R² is negative — persistence is worse than guessing the mean (headline CPI mean-reverts).
- 0.18pp RMSE = systematic multi-month edge, NOT single-print precision (pro consensus ~0.12pp).
