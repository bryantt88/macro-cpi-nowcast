## COMPACT — 2026-09-10 (covers since 2026-09-07)

**In one line:** Refined the feature set (dropped redundant PPIFIS, added lagged energy) — skill rose 39.6% → 42.8%, holds on the robustness run — and scoped the next step: benchmark vs the Cleveland Fed nowcast.

### WHAT CHANGED
- Dropped `ppifis_mom_lag1` from `features/build.py` → skill 39.6%→41.5%. It was 54% missing (starts 2014-04), 0.80-corr with `ppi_mom_lag1` (PPIACO, full history), and caused an imputer warning + inconsistent ridge feature count every pre-2014 fold.
- Confirmed the drop: re-adding headline PPI (PPIFIS) to LightGBM-only = dead tie; to both models = worse. PPIACO already carries the producer-price signal. **PPIACO is NOT the headline PPI print — it's the long-history All-Commodities cousin (0.80 corr).**
- Added lagged energy (`wti_mom_lag1`, `gasoline_mom_lag1`) to `features/build.py` → skill 41.5%→42.8%. Economic basis: oil/gasoline pass through to some CPI components (airfares, plastics, freight) ~1 month late.
- Weak-year cause found: low skill years are either quiet/low-vol (2014, 2024 — naive already near-optimal, nothing to win) or regime breakouts (2021 surge — model mean-reverts while inflation runs). Honest, expected weakness — not overfitting.

### WHERE THINGS STAND
- Model = ridge + shallow LightGBM + mean ensemble, **19 features**. PRIMARY (196 mo, 2010–2026): ens RMSE **0.175**, skill **42.8%**, hit 68.9%, dir 79.6%. ROBUSTNESS (232 mo, 2007-start): skill **42.1%**, hit 69.4%. 9/9 tests pass. `oos_predictions` table refreshed.

### DO NEXT
1. Pull the **Cleveland Fed CPI MoM nowcast** history (~2016 real-time archive — free, same monthly frequency, same inputs as ours) and score our model against it. This tells us if we're consensus-grade, not just beating the dumb guess.
2. Then Stage 5 (report).
- Blocked on: nothing. (Cleveland Fed has no clean CSV — extract via chart JSON / MacroMicro / email.)

### DECISIONS LOCKED
- Drop PPIFIS; keep PPIACO for producer prices. — redundant + half-missing + hurt skill.
- Lagged energy stays. — improves both primary AND robustness = real, not fluke.
- Benchmark = Cleveland Fed nowcast (monthly). — SPF rejected (quarterly/annual, wrong frequency); scraping TradingEconomics/Investing rejected (ToS + brittle + not reproducible); true economist monthly consensus = paid, parked.
