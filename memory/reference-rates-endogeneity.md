# Reference — OIS / rate futures vs inflation (causality & why parked)

**Status:** parked idea, not in the current build. Revisit if we want a "market-expectations" angle later.

## The insight (Bryant's, 2026-08-19)
Causality runs **inflation → Fed-path expectations → OIS curve & fed funds/SOFR futures**, not the
reverse (at least on the horizon we care about). OIS and rate futures are the market's *expected policy
path* — they move **because** inflation surprises re-price the Fed, so they are **downstream of
inflation**, not an independent driver of it.

- The reverse effect (rates cooling inflation) is real but **slow — 12–18 month lag** → useless for
  predicting **next month's** CPI print.
- OIS / rate futures ≈ "the market's own inflation forecast, repackaged as a rate."

## Why they're NOT in the current CPI model
1. **Circularity / endogeneity** — feeding an inflation-expectations proxy into a CPI predictor is
   partly predicting inflation *with* an inflation forecast → false sense of accuracy.
2. **Free-data rule** — clean OIS / rate-futures curves aren't reliably free (cuts against the
   free-sources constraint). Our spec uses FRED **spot** rates (fed funds, 2y, 10y, 10y−2y slope).
3. For a next-month **headline** CPI nowcast, real-time **energy/gasoline, commodities, DXY, ISM
   prices-paid** carry the mechanical signal; rate expectations only *echo* inflation back.

## How we might explore it later (if we revisit)
- Test whether **rate-expectation surprises** (not levels) add any residual signal after energy/commodity
  features — i.e. does the market know something CPI-relevant that our real-time inputs miss?
- Use OIS/futures as a **regime / cross-check** variable rather than a direct predictor.
- Only pursue if a **free** source for the curve is found; otherwise it breaks the free-data rule.

See also [[project-roadmap]] (data sources = FRED spot rates; anti-overfitting protocol).
